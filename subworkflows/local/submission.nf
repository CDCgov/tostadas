#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION                                    } from '../../modules/local/initial_submission/main'
include { FETCH_SUBMISSION                              } from '../../modules/local/fetch_submission/main'
include { UPDATE_SUBMISSION                             } from '../../modules/local/update_submission/main'
include { WAIT                                          } from '../../modules/local/general_util/wait/main'
include { MERGE_UPLOAD_LOG                              } from "../../modules/local/general_util/merge_upload_log/main"

workflow INITIAL_SUBMISSION {
    take:
        submission_ch         // (meta: [batch_id: ...], samples: [ [meta, fasta, fq1, fq2, gff], ... ])
        submission_config
        wait_time

    main:
        submission_config_file = file(submission_config)
        // Declare channels to dynamically handle conditional process outputs
        Channel.empty().set { submission_files } // Default for SUBMISSION output
        Channel.empty().set { update_files } // Default for UPDATE_SUBMISSION output

        WAIT(wait_time)

        def resolved_output_dir = params.output_dir.startsWith('/') ? params.output_dir : "${baseDir}/${params.output_dir}"

        if (params.fetch_reports_only == true) {
            // Check if submission folder exists and run report fetching module
            submission_ch.map { meta, samples ->
                def submission_folder = file("${resolved_output_dir}/${params.submission_output_dir}/${meta.batch_id}")
                if (!submission_folder.exists()) {
                    throw new IllegalStateException("Submission folder does not exist for batch: ${meta.batch_id}")
                }
                return tuple(meta, samples, submission_folder)
            }
            .set { batch_with_folder }

            FETCH_SUBMISSION(WAIT.out, batch_with_folder, submission_config_file)
                .set { fetched_reports }
        } else {
            submission_ch
                .map { meta, samples ->
                    def enabledDatabases = [] as Set
                    def missingFiles = [] as Set

                    samples.each { s ->
                        if (params.sra) {
                            if (!s.fq1 || !file(s.fq1).exists()) missingFiles << "${s.meta.id}:fastq_1"
                            if (!s.fq2 || !file(s.fq2).exists()) missingFiles << "${s.meta.id}:fastq_2"
                            else enabledDatabases << "sra"
                        }
                        if (params.genbank) {
                            if (!s.fasta || !file(s.fasta).exists()) missingFiles << "${s.meta.id}:fasta"
                            if (!s.gff || !file(s.gff).exists()) missingFiles << "${s.meta.id}:gff"
                            else enabledDatabases << "genbank"
                        }
                        if (params.biosample) {
                            enabledDatabases << "biosample"
                        }
                    }

                    if (!missingFiles) {
                        return tuple(meta, samples, enabledDatabases.toSorted().unique())
                    } else {
                        log.warn "Skipping batch ${meta.batch_id} due to missing files: ${missingFiles.join(', ')}"
                        return null
                    }
                }
                .filter { it != null }
                .set { valid_batches }
                
            valid_batches.view { println "valid_batches -> ${it}" }

            if (!params.update_submission) {
                SUBMISSION(valid_batches, submission_config_file)
                    .set { submission_files }

            // some other processes go here (FETCH, UPDATE)
            } 
        } 

    emit:
        submission_files = submission_files
        update_files = update_files
        //fetched_reports = fetched_reports
}
