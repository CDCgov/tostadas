// Global variable to uniquely identify a run by its metadata filename
params.metadata_basename = file(params.meta_path).baseName

include { BIOSAMPLE_AND_SRA         } from './workflows/biosample_and_sra'
include { GENBANK                   } from './workflows/genbank'
include { BIOSAMPLE_UPDATE          } from './workflows/biosample_update'
include { AGGREGATE_SUBMISSIONS     } from './subworkflows/local/aggregate_submissions'
include { WAIT                      } from './modules/local/wait/main'

// Function to calculate time to wait between submitting and fetching report.xml
def calc_wait_time() {
    return params.submission_wait_time != 'calc'
        ? params.submission_wait_time as int
        : 30 * params.batch_size as int
}

workflow BIOSAMPLE_AND_SRA_WORKFLOW {
    BIOSAMPLE_AND_SRA()
    if (params.submission) {
        WAIT( BIOSAMPLE_AND_SRA.out.submission_batch_folder.map { calc_wait_time() } )
        AGGREGATE_SUBMISSIONS(BIOSAMPLE_AND_SRA.out.submission_batch_folder, 
                            params.submission_config,
                            BIOSAMPLE_AND_SRA.out.validated_concatenated_tsv,
                            WAIT.out)
    }
}

workflow GENBANK_WORKFLOW {
    // Set default for updated_meta_path if not already defined
    def updated_meta_file = params.updated_meta_path && params.updated_meta_path != '' ?
        file(params.updated_meta_path) :
        file("${params.outdir}/${params.metadata_basename}/${params.final_submission_outdir}/${params.metadata_basename}_updated.xlsx")

    // Log an error if the updated metadata file doesn't exist
    if (!updated_meta_file.exists()) {
                log.error "Required file not found for genbank workflow: ${updated_meta_file}"
                exit 1
            } else {
                log.info "Found required updated metadata file: ${updated_meta_file}"
            }

    GENBANK(file(updated_meta_file))
    if (params.organism_type in ['sars', 'flu', 'bacteria', 'eukaryote']) {
        WAIT( GENBANK.out.submission_batch_folder.map { calc_wait_time() } )
        AGGREGATE_SUBMISSIONS(GENBANK.out.submission_batch_folder,
                            params.submission_config,
                            file("${params.outdir}/${params.metadata_basename}/${params.validation_outdir}/validated_metadata_all_samples.tsv"), WAIT.out)
    }
}

workflow FETCH_ACCESSIONS_WORKFLOW {
    // glob for all subdirectories starting with "batch_" and collect into one list
    batches = Channel.fromPath(
        "${params.outdir}/${params.metadata_basename}/${params.submission_outdir}/batch_*",
        type: 'dir'
    ).map { dir ->
        def meta = [ batch_id: dir.baseName ]
        tuple(meta, dir)
    } // meta = batch_id, dir = path to batch_id dir
    log.info "Fetching report.xml files for submissions in ${params.outdir}/${params.metadata_basename}/${params.submission_outdir}"
    // use a dummy channel placeholder in place of the WAIT utility, which isn't used in this workflow, 
    dummy_wait = Channel.value(true)
    AGGREGATE_SUBMISSIONS(batches,
                          params.submission_config,
                          file("${params.outdir}/${params.metadata_basename}/${params.validation_outdir}/validated_metadata_all_samples.tsv"), dummy_wait)
}

workflow UPDATE_SUBMISSION_WORKFLOW {
    BIOSAMPLE_UPDATE()
}

workflow {
    if (params.workflow == "full_submission") {
        BIOSAMPLE_AND_SRA()
        WAIT( BIOSAMPLE_AND_SRA.out.submission_batch_folder.map { calc_wait_time() } )
        AGGREGATE_SUBMISSIONS(BIOSAMPLE_AND_SRA.out.submission_batch_folder, params.submission_config, BIOSAMPLE_AND_SRA.out.validated_concatenated_tsv, WAIT.out)
        GENBANK(AGGREGATE_SUBMISSIONS.out.accession_augmented_xlsx)
    }
    else if (params.workflow == "biosample_and_sra") {
        BIOSAMPLE_AND_SRA_WORKFLOW()
    }
    else if (params.workflow == "genbank") {
        GENBANK_WORKFLOW()
    }
    else if (params.workflow == "fetch_accessions") {
        FETCH_ACCESSIONS_WORKFLOW()
    }
    else if (params.workflow == "update_submission") {
        UPDATE_SUBMISSION_WORKFLOW()
    }
    else {
        error "Invalid workflow specified."
    }
}
