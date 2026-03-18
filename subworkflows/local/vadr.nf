#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            VADR SUBWORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { VADR_MODEL_SETUP                                  } from "../../modules/local/vadr_model_setup/main"
include { VADR_TRIM                                         } from "../../modules/local/vadr_trim/main"
include { VADR_ANNOTATION                                   } from "../../modules/local/vadr_annotation/main"
include { VADR_POST_CLEANUP                                 } from "../../modules/local/vadr_post_cleanup/main"

workflow RUN_VADR {
    take:
        fasta // meta, fasta_path

    main:
        // Pre-flight check: verify that the VADR model directory is compatible
        // with the specified virus_subtype. Catches user misconfiguration early
        // (e.g. pointing vadr_models_dir at RSV models while virus_subtype=mev)
        // rather than letting VADR fail with a cryptic error downstream.
        def models_dir = file(params.vadr_models_dir)
        def expected_cm = "${params.virus_subtype}.cm"
        def cm_file    = models_dir.resolve(expected_cm)
        def cm_url     = params.vadr_cm_url ?: ''

        if (models_dir.exists()) {
            def cm_files_found = models_dir.listFiles()
                .findAll { it.name.endsWith('.cm') }
                .collect { it.name }

            // Only raise a mismatch error when the directory contains .cm files
            // for a different subtype but not the expected one, and no download
            // URL is configured. If the directory has no .cm files at all,
            // VADR_MODEL_SETUP handles that case (download or error).
            if (cm_files_found && !cm_file.exists() && !cm_url) {
                error """
                    ==========================================================================
                    VADR MODEL / VIRUS SUBTYPE MISMATCH
                    ==========================================================================
                    VADR model directory does not contain a model matching
                    virus_subtype '${params.virus_subtype}'.
                    Expected file : ${models_dir}/${expected_cm}
                    Found CM files: ${cm_files_found.join(', ')}

                    To fix this, either:
                      1. Set 'vadr_models_dir' to a directory that contains '${expected_cm}', or
                      2. Set 'vadr_cm_url' so the correct CM file can be downloaded.
                    ==========================================================================
                    """.stripIndent()
            }
        }

        // Step 0: Ensure model directory is ready (downloads CM if needed, builds indices)
        VADR_MODEL_SETUP(params.vadr_models_dir)

        // Step 1: Trim terminal ambiguous nucleotides from fasta
        VADR_TRIM(fasta)

        // Step 2: Run VADR annotation on trimmed fasta
        VADR_ANNOTATION(
            VADR_TRIM.out.trimmed_fasta,
            VADR_MODEL_SETUP.out.prepared_models
        )

        // Step 3: Post-process VADR outputs
        VADR_POST_CLEANUP(VADR_ANNOTATION.out.vadr_outputs)

    emit:
        gff    = VADR_POST_CLEANUP.out.gff      // tuple val(meta), path('*/gffs/*.gff')
        errors = VADR_POST_CLEANUP.out.errors   // tuple val(meta), path('*/errors/*.txt')
        tbl    = VADR_POST_CLEANUP.out.tbl      // tuple val(meta), path('*/tbl/*.tbl')
}