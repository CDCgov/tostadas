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
        submission_ch // meta.id, tsv, fasta, fastq1, fastq2, gff
        submission_config
        wait_time

    main:
        // Declare channels to dynamically handle conditional process outputs
        Channel.empty().set { submission_files }    // Default for SUBMISSION output
        Channel.empty().set { update_files }        // Default for UPDATE_SUBMISSION output
        Channel.empty().set { fetched_reports }     // Default for FETCH_SUBMISSION output
        // actual process to initiate wait 
        //WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )
        WAIT ( wait_time )

        if ( params.fetch_reports_only == true ) {
            // Check if submission folder exists and run report fetching module
            submission_ch
                    .map { meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path -> 
                        def folder_path = file("${params.output_dir}/${params.submission_output_dir}/${meta.id}")
                        if (!folder_path.exists()) {
                            throw new IllegalStateException("Submission folder does not exist for ID: ${meta.id}")
                        }
                        // Return the tuple unchanged if the folder exists
                        return tuple(meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path)
                    }
                    .set { valid_submission_ch } // Create a new validated channel

            FETCH_SUBMISSION ( WAIT.out, valid_submission_ch, submission_config )
                .set { fetched_reports }
        }

        else if ( params.update_submission == false ) {
            // submit the files to database of choice
            SUBMISSION ( submission_ch, submission_config )
                .set { submission_files }

            // try to fetch & parse the report.xml
            // todo: this maybe doesn't need to take all the inputs from submission (or maybe doesn't need to be a separate module)
            FETCH_SUBMISSION ( WAIT.out, submission_ch, submission_config )
                .set { fetched_reports }
        }

        // if params.update_submission is true, update an existing submission
        else if ( params.update_submission == true ) {
            // process for updating the submitted samples
            UPDATE_SUBMISSION ( submission_ch, submission_config )
                .set { update_files }

            // try to fetch & parse the report.xml
            FETCH_SUBMISSION ( WAIT.out, submission_ch, submission_config )
                .set { fetched_reports }
        }
        
    emit:
        submission_files = submission_files
        update_files = update_files
        fetched_reports = fetched_reports
        //submission_files = SUBMISSION.out.submission_files
        //submission_log = SUBMISSION.out.submission_log

        //to do: add GISAID module
}
