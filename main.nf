// Global variable to uniquely identify a run by its metadata filename
params.metadata_basename = file(params.meta_path).baseName

include { BIOSAMPLE_AND_SRA         } from './workflows/biosample_and_sra'
include { GENBANK                   } from './workflows/genbank'
include { BIOSAMPLE_UPDATE          } from './workflows/biosample_update'
include { AGGREGATE_SUBMISSIONS     } from './subworkflows/local/aggregate_submissions'

workflow BIOSAMPLE_AND_SRA_WORKFLOW {
    BIOSAMPLE_AND_SRA()
    if (params.submission) {
        AGGREGATE_SUBMISSIONS(BIOSAMPLE_AND_SRA.out.submission_batch_folder,
                            params.submission_config,
                            BIOSAMPLE_AND_SRA.out.validated_concatenated_tsv)
    }
}

workflow GENBANK_WORKFLOW {
    // In genbank_only mode, use meta_path directly (no prior BioSample/SRA run needed)
    def updated_meta_file = params.genbank_only ?
        file(params.meta_path) :
        params.updated_meta_path && params.updated_meta_path != '' ?
            file(params.updated_meta_path) :
            file("${params.outdir}/${params.accessions_outdir}/${params.metadata_basename}_updated.xlsx")

    // Log an error if the updated metadata file doesn't exist
    if (!updated_meta_file.exists()) {
                log.error "Required file not found for genbank workflow: ${updated_meta_file}"
                exit 1
            } else {
                log.info "Found required updated metadata file: ${updated_meta_file}"
            }

    GENBANK(file(updated_meta_file))

    // GenBank processing takes days to weeks depending on organism type.
    // Accessions must be fetched separately after NCBI finishes processing.
    if (params.submission) {
        log.info "GenBank submission complete. Run '--workflow fetch_accessions' after NCBI has processed your submission to retrieve accessions."
    }
}

workflow FETCH_ACCESSIONS_WORKFLOW {
    // GenBank submissions are stored under a genbank/ subdirectory;
    // biosample/SRA submissions are stored directly under submission_outdir.
    def base_dir = "${params.outdir}/${params.submission_outdir}"
    def genbank_dir = "${base_dir}/genbank"
    def search_dir = file(genbank_dir).isDirectory() ? genbank_dir : base_dir

    batches = Channel.fromPath(
        "${search_dir}/batch_*",
        type: 'dir'
    ).map { dir ->
        def meta = [ batch_id: dir.baseName ]
        tuple(meta, dir)
    }
    log.info "Fetching report.xml files for submissions in ${search_dir}"
    AGGREGATE_SUBMISSIONS(batches,
                          params.submission_config,
                          file("${params.outdir}/${params.validation_outdir}/validated_metadata_all_samples.tsv"))
}

workflow UPDATE_SUBMISSION_WORKFLOW {
    BIOSAMPLE_UPDATE()
}

workflow {
    if (params.workflow == "full_submission") {
        BIOSAMPLE_AND_SRA()
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
    else if (params.workflow == "update_submission") {
        UPDATE_SUBMISSION_WORKFLOW()
    }
    else {
        error "Invalid workflow specified."
    }
}
