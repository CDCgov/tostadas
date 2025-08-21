/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                CHECK VALIDATION ERRORS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process CHECK_VALIDATION_ERRORS {

    input:
    path error_file

    output:
    stdout emit: status

    script:
    """
    if grep -q "ERROR" $error_file; then
        echo -n "ERROR"
    else
        echo -n "OK"
    fi
    """ 
}