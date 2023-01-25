import os 


class TestNFDatabaseSubmission():
    def __init__(self):
        self.databases = ['genbank', 'sra', 'gisaid', 'biosample', 'joint_sra_biosample']

    def test_main(self): 
        # get the nextflow outputs to use for the submission part only 
        os.system("nextflow run main.nf -profile test,conda --with_submission False --submission_wait_time 2")

        # run the submission entrypoint with passing only one of the database entries 
        for database in self.databases:
            os.system("nextflow run main.nf -profile test,conda -entry only_submission --submission_database {database} --submission_wait_time 2")
            # confirm that the output is correct (only the files for the database)
            self.check_outputs(database_name=database)

        # delete outputs and repeat #2-#4 for remaining 
    
    @staticmethod
    def check_outputs(database_name):
        assert os.path.exists()
        
    
    @staticmethod 
    def delete_outputs():
        """
        """


if __name__ == "__main__":
    test_main()