include { BIOSAMPLE_AND_SRA } from './workflows/biosample_and_sra'
include { GENBANK } from './workflows/genbank'

workflow BIOSAMPLE_AND_SRA_WORKFLOW {
    BIOSAMPLE_AND_SRA()
}

workflow FETCH_ACCESSIONS_WORKFLOW {
    FETCH_ACCESSIONS(file(params.submission_results_dir))
}

workflow GENBANK_WORKFLOW {
    GENBANK()
}


workflow {
    if (params.workflow == "biosample_and_sra") {
        BIOSAMPLE_AND_SRA_WORKFLOW()
        FETCH_ACCESSIONS_WORKFLOW()
    }
    else if (params.workflow == "fetch_accessions") {
        FETCH_ACCESSIONS_WORKFLOW()
    }
    else if (params.workflow == "genbank") {
        GENBANK_WORKFLOW()
    }
    else {
        error "Invalid workflow specified..."
    }
}
