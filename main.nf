// Global variable to uniquely identify a run by its metadata filename
params.metadata_basename = file(params.meta_path).baseName
// Set default for updated_meta_path if not already defined
params.updated_meta_path = params.updated_meta_path ?: "${params.outdir}/${params.metadata_basename}/${params.final_submission_output_dir}/${params.metadata_basename}_updated.xlsx"

include { BIOSAMPLE_AND_SRA         } from './workflows/biosample_and_sra'
include { GENBANK                   } from './workflows/genbank'
include { AGGREGATE_SUBMISSIONS     } from './subworkflows/local/aggregate_submissions'
include { WAIT                      } from './modules/local/wait/main'

// Function to calculate time to wait between submitting and fetching report.xml
def calc_wait_time() {
    return params.submission_wait_time != 'calc'
        ? params.submission_wait_time as int
        : 3 * 60 * params.batch_size as int
}

workflow BIOSAMPLE_AND_SRA_WORKFLOW {
    BIOSAMPLE_AND_SRA()
    AGGREGATE_SUBMISSIONS(BIOSAMPLE_AND_SRA.out.submission_batch_folder, 
                          params.submission_config,
                          BIOSAMPLE_AND_SRA.out.validated_concatenated_tsv)
}

workflow GENBANK_WORKFLOW {
    GENBANK(file(params.updated_meta_path))
    if (params.species in ['sars', 'flu', 'bacteria', 'eukaryote']) {
        AGGREGATE_SUBMISSIONS(GENBANK.out.submission_batch_folder,
                            params.submission_config,
                            file("${params.outdir}/${params.metadata_basename}/${params.val_output_dir}/validated_metadata_all_samples.tsv"))
    }
}

workflow FETCH_ACCESSIONS_WORKFLOW {

    // glob for all subdirectories starting with "batch_" and collect into one list
    batches = Channel.fromPath(
        "${params.outdir}/${params.metadata_basename}/${params.submission_output_dir}/batch_*",
        type: 'dir'
    ).map { dir ->
        def meta = [ batch_id: dir.baseName ]
        tuple(meta, dir)
    } // meta = batch_id, dir = path to batch_id dir
    
    batches.view { "DEBUG - BATCHES: $it" }
    log.info "Fetching report.xml files for submissions in ${params.outdir}/${params.metadata_basename}/${params.submission_output_dir}"
    

    AGGREGATE_SUBMISSIONS(batches,
                          params.submission_config,
                          file("${params.outdir}/${params.metadata_basename}/${params.val_output_dir}/validated_metadata_all_samples.tsv"))

}

workflow {
    if (params.workflow == "full_submission") {
        BIOSAMPLE_AND_SRA()
        WAIT( Channel.value( calc_wait_time() ) )
        AGGREGATE_SUBMISSIONS(BIOSAMPLE_AND_SRA.out.submission_batch_folder, params.submission_config, BIOSAMPLE_AND_SRA.out.validated_concatenated_tsv)
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
    else {
        error "Invalid workflow specified."
    }
}
