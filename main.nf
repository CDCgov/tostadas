include { BIOSAMPLE_AND_SRA         } from './workflows/biosample_and_sra'
include { GENBANK                   } from './workflows/genbank'
include { FETCH_ACCESSIONS          } from './subworkflows/local/fetch_accessions'

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
        FETCH_ACCESSIONS(BIOSAMPLE_AND_SRA.out.submission_folders, params.submission_config)
        GENBANK(BIOSAMPLE_AND_SRA.out.enriched_tsvs)
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
