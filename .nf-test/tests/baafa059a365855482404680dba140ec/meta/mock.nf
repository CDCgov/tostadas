import groovy.json.JsonGenerator
import groovy.json.JsonGenerator.Converter

nextflow.enable.dsl=2

// comes from nf-test to store json files
params.nf_test_output  = ""

// include dependencies


// include test process
include { PREP_SUBMISSION } from '/scicomp/home-pure/rjd0/tostadas/modules/local/prep_submission/main.nf'

// define custom rules for JSON that will be generated.
def jsonOutput =
    new JsonGenerator.Options()
        .addConverter(Path) { value -> value.toAbsolutePath().toString() } // Custom converter for Path. Only filename
        .build()

def jsonWorkflowOutput = new JsonGenerator.Options().excludeNulls().build()


workflow {

    // run dependencies
    

    // process mapping
    def input = []
    
                // define inputs of the process here
                input[0] = [ [batch_id: 'batch_1', batch_tsv: file("/scicomp/home-pure/rjd0/tostadas/tests/modules/local/prep_submission/batch_1.tsv")], 
                             [ [meta: [ sample_id: 'NY0006' ], fq1: file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastqs/mpox/2022-028-7666_S3_L001_R1_001.fastq.gz"), fq2: file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastqs/mpox/2022-028-7666_S3_L001_R2_001.fastq.gz"), fasta: file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastas/mpox/NY0006.fasta"), nnp: null, gff: null], 
                               [meta: [ sample_id: 'IL0005' ], fq1: file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastqs/mpox/LIY15306A2_2022_054_3005007722.R_1.mpx.fastq.gz"), fq2: file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastqs/mpox/LIY15306A2_2022_054_3005007722.R_2.mpx.fastq.gz"), fasta: file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastas/mpox/IL0005.fasta"), nnp: null, gff: null]
                             ], 
                             ["biosample"] ]
                input[1] = file("/scicomp/home-pure/rjd0/tostadas/conf/submission_config.yaml")
                
    //----

    //run process
    PREP_SUBMISSION(*input)

    if (PREP_SUBMISSION.output){

        // consumes all named output channels and stores items in a json file
        for (def name in PREP_SUBMISSION.out.getNames()) {
            serializeChannel(name, PREP_SUBMISSION.out.getProperty(name), jsonOutput)
        }	  
      
        // consumes all unnamed output channels and stores items in a json file
        def array = PREP_SUBMISSION.out as Object[]
        for (def i = 0; i < array.length ; i++) {
            serializeChannel(i, array[i], jsonOutput)
        }    	

    }
  
}

def serializeChannel(name, channel, jsonOutput) {
    def _name = name
    def list = [ ]
    channel.subscribe(
        onNext: {
            list.add(it)
        },
        onComplete: {
              def map = new HashMap()
              map[_name] = list
              def filename = "${params.nf_test_output}/output_${_name}.json"
              new File(filename).text = jsonOutput.toJson(map)		  		
        } 
    )
}


workflow.onComplete {

    def result = [
        success: workflow.success,
        exitStatus: workflow.exitStatus,
        errorMessage: workflow.errorMessage,
        errorReport: workflow.errorReport
    ]
    new File("${params.nf_test_output}/workflow.json").text = jsonWorkflowOutput.toJson(result)
    
}
