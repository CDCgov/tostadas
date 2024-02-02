/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                CLEANUP FILES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process CLEANUP_FILES {
    input:
        val signal
    exec:
        // clear all .nextflow.log files
        if ( params.clear_nextflow_log == true ) {
            dir = file("$projectDir")
            list_of_log_files = dir.listFiles()
            for ( def file : list_of_log_files ) {
                file_stripped = file.getBaseName()
                if( file_stripped == ".nextflow.log" ) {
                    file.setPermissions('rwxr-xr-x')
                    file.delete()
                    try {
                        assert dir.isFile() == false
                    } catch(Exception e) {
                        throw new Exception("Did not properly delete the work directory")
                    }
                }
            }
        }

        // clear all work subdirectories except for conda if present
        dir = file("$workDir")
        if ( params.clear_work_dir == true && dir.isDirectory() == true ) {
            dir.eachFile {
                if ( it.getSimpleName() != 'conda' ) {
                    it.setPermissions('rwxr-xr-x')
                    it.deleteDir()
                }
            }
        }

        // clear conda env inside of work directory
        dir = file("$workDir")
        if ( params.clear_conda_env == true && dir.isDirectory() ) {
            dir.eachFile {
                if ( it.getSimpleName() == 'conda' ) {
                    it.setPermissions('rwxr-xr-x')
                    it.deleteDir()
                }
            }
        }

        // clear nextflow results completely
        dir = file("$params.output_dir")
        if ( params.clear_nf_results == true && dir.isDirectory() == true ) {
            dir.setPermissions('rwxr-xr-x')
            dir.deleteDir()
            try {
                assert dir.isDirectory() == false
            } catch(Exception e) {
                throw new Exception("Nextflow results directory was not properly deleted: $params.output_dir")
            }
        }
    output:
        val true
}