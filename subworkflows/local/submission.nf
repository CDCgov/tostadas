#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { PREP_SUBMISSION                               } from '../../modules/local/prep_submission/main'
include { SUBMIT_SUBMISSION                             } from '../../modules/local/submit_submission/main'
include { FETCH_SUBMISSION                              } from '../../modules/local/fetch_submission/main'
include { UPDATE_SUBMISSION                             } from '../../modules/local/update_submission/main'
include { AGGREGATE_REPORTS                             } from '../../modules/local/aggregate_reports/main'
include { WAIT                                          } from '../../modules/local/general_util/wait/main'
include { MERGE_UPLOAD_LOG                              } from "../../modules/local/general_util/merge_upload_log/main"

workflow INITIAL_SUBMISSION {
    take:
        submission_ch         // (meta: [batch_id: ..., batch_tsv: ...], samples: [ [meta, fasta, fq1, fq2, nnp, gff], ... ]), enabledDatabases (list)
        submission_config
        wait_time

    main:
        submission_config_file = file(submission_config)
        // Declare channels to dynamically handle conditional process outputs
        Channel.empty().set { submission_files } // Default for SUBMISSION output
        Channel.empty().set { update_files } // Default for UPDATE_SUBMISSION output

        WAIT(wait_time)

        if (params.fetch_reports_only == true) {
            // Check if submission folder exists and run report fetching module
            submission_ch.map { meta, samples, enabledDatabases ->
                def resolved_output_dir = params.output_dir.startsWith('/') ? params.output_dir : "${baseDir}/${params.output_dir}"
                def submission_folder = file("${resolved_output_dir}/${params.submission_output_dir}/${params.metadata_basename}/${meta.batch_id}") 
                if (!submission_folder.exists()) {
                    throw new IllegalStateException("Submission folder does not exist for batch: ${meta.batch_id}")
                }
                return tuple(meta, samples, enabledDatabases, submission_folder)
            }
            .set { batch_with_folder }

            FETCH_SUBMISSION(WAIT.out, batch_with_folder, submission_config_file)

            // Collect all fetched per-batch CSV reports
            FETCH_SUBMISSION.out.submission_report
                .collect()
                .set { all_report_csvs }

            // Aggregate all of them
            AGGREGATE_REPORTS(all_report_csvs)

        } else {
            if (params.update_submission == false) {
                PREP_SUBMISSION(submission_ch, submission_config_file)
                    .set { submission_files }

                SUBMIT_SUBMISSION(submission_files, submission_config_file)
            
                submission_ch.join(submission_files)
                    .map { meta, samples, enabledDatabases, submission_folder ->
                        return tuple(meta, samples, enabledDatabases, submission_folder)
                    }
                    .set {submission_with_folder}

                FETCH_SUBMISSION ( WAIT.out, submission_with_folder, submission_config_file )

                // Collect all fetched per-batch CSV reports
                FETCH_SUBMISSION.out.submission_report
                    .collect()
                    .set { all_report_csvs }

                // Aggregate all of them
                AGGREGATE_REPORTS(all_report_csvs)
                } 

            //if (params.update_submission == true) {
            //    UPDATE_SUBMISSION(submission_ch, submission_config_file)  
            //}

        } 

    emit:
        all_report_csvs = all_report_csvs
        //submission_files = submission_files
        //update_files = update_files
        //fetched_reports = fetched_reports
}
