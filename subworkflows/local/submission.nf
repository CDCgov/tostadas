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
    submission_config_file = file(submission_config)

    take:
        submission_ch // meta.id, tsv, fasta, fastq1, fastq2, gff
        submission_config
        wait_time

    main:
        // Declare channels to dynamically handle conditional process outputs
        Channel.empty().set { submission_files }    // Default for SUBMISSION output
        Channel.empty().set { update_files }        // Default for UPDATE_SUBMISSION output

        // actual process to initiate wait 
        //WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )
        WAIT ( wait_time )

        def resolved_output_dir = params.output_dir.startsWith('/') ? params.output_dir : "${baseDir}/${params.output_dir}"
        //def submission_folder = file("${resolved_output_dir}/${params.submission_output_dir}/${meta.id}")
        
        if ( params.fetch_reports_only == true ) {
            // Check if submission folder exists and run report fetching module
            submission_ch = submission_ch
                .map { meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path -> 
                    def submission_folder = file("${resolved_output_dir}/${params.submission_output_dir}/${meta.id}")
                    if (!submission_folder.exists()) {
                        throw new IllegalStateException("Submission folder does not exist for ID: ${meta.id}")
                    }
                    return tuple(meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path, submission_folder)
                }
            FETCH_SUBMISSION ( WAIT.out, submission_ch, submission_config_file )
                .set { fetched_reports }
        }

        else {
            submission_ch = submission_ch
                .map { meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path ->
                    def missingFiles = []
                    def enabledDatabases = []

                    // Check SRA requirements
                    if (params.sra) {
                        if (!fastq_1 || !file(fastq_1).exists()) missingFiles << "fastq_1"
                        if (!fastq_2 || !file(fastq_2).exists()) missingFiles << "fastq_2"
                        if (!missingFiles) enabledDatabases << "sra"
                    }

                    // Check GenBank requirements
                    if (params.genbank) {
                        if (!fasta_path || !file(fasta_path).exists()) missingFiles << "fasta"
                        if (!annotations_path || !file(annotations_path).exists()) missingFiles << "annotation"
                        if (!missingFiles) enabledDatabases << "genbank"
                    }

                    // BioSample does not require additional files
                    if (params.biosample) {
                        enabledDatabases << "biosample"
                    }

                    log.info "DEBUG: enabledDatabases for ${meta.id} -> ${enabledDatabases}"
                    if (missingFiles) {
                        log.warn "Skipping databases due to missing files for sample ${meta.id}: ${missingFiles.join(', ')}"
                    }
                    return tuple(meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path, enabledDatabases)
                }

            if (params.update_submission == false) {
                submission_ch.view() 
                submission_ch.view { entry ->
                    println "DEBUG: filtered_submission_ch structure -> ${entry}"
                }

                SUBMISSION (submission_ch, submission_config_file)
                    .set { submission_files }

                submission_ch.join(submission_files)
                    .map { meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path, enabledDatabases, submission_folder -> 
                        return tuple(meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path, enabledDatabases, submission_folder)
                    }
                    .set { submission_with_folder }

                FETCH_SUBMISSION ( WAIT.out, submission_with_folder, submission_config_file )
                    .set { fetched_reports }
            }

            if (params.update_submission == true) {

                UPDATE_SUBMISSION (submission_ch, submission_config_file)
                    .set { update_files }

                // Map submission_ch to include submission_folder (from UPDATE_SUBMISSION.out.submission_files)
                //submission_ch = submission_ch
                //    .map { meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path -> 
                //        return tuple(meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path, UPDATE_SUBMISSION.out.submission_files)
                //    }

                submission_ch.join(update_files)
                    .map { meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path, enabledDatabases, submission_folder -> 
                        return tuple(meta, validated_meta_path, fasta_path, fastq_1, fastq_2, annotations_path, enabledDatabases, submission_folder)
                    }
                    .set { submission_with_folder }

                FETCH_SUBMISSION ( WAIT.out, submission_with_folder, submission_config_file )
                    .set { fetched_reports }
            }
        }
        
    emit:
        submission_files = submission_files
        update_files = update_files
        fetched_reports = fetched_reports
}
