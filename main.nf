// Global variable to uniquely identify a run by its metadata filename
params.metadata_basename = file(params.meta_path).baseName

include { BIOSAMPLE_AND_SRA         } from './workflows/biosample_and_sra'
include { GENBANK                   } from './workflows/genbank'
include { FETCH_ACCESSIONS          } from './subworkflows/local/fetch_accessions'
include { WAIT                      } from './modules/local/wait/main'

// Function to calculate time to wait between submitting and fetching report.xml
def calc_wait_time() {
    return params.submission_wait_time != 'calc'
        ? params.submission_wait_time as int
        : 3 * 60 * params.batch_size as int
}

workflow BIOSAMPLE_AND_SRA_WORKFLOW {
    BIOSAMPLE_AND_SRA()
    FETCH_ACCESSIONS(BIOSAMPLE_AND_SRA.out.submission_folders, params.submission_config)
    // AGGREGATE_REPORTS could go here after FETCH_ACCESSIONS
}

workflow GENBANK_WORKFLOW {
    GENBANK()
    FETCH_ACCESSIONS(GENBANK.out.submission_folders, params.submission_config)
    // AGGREGATE_REPORTS could go here after FETCH_ACCESSIONS
}

workflow FETCH_ACCESSIONS_WORKFLOW {
    FETCH_ACCESSIONS(file(params.submission_results_dir), params.submission_config)
}

workflow {
    if (params.workflow == "full_submission") {
        BIOSAMPLE_AND_SRA()
        WAIT( Channel.value( calc_wait_time() ) )
        FETCH_ACCESSIONS(BIOSAMPLE_AND_SRA.out.submission_folders, params.submission_config)
        GENBANK(BIOSAMPLE_AND_SRA.out.enriched_tsvs)
        WAIT( Channel.value( calc_wait_time() ) )
        FETCH_ACCESSIONS(GENBANK.out.submission_folders, params.submission_config)
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
