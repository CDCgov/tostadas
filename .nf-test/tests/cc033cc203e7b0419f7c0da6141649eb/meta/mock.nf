import groovy.json.JsonGenerator
import groovy.json.JsonGenerator.Converter

nextflow.enable.dsl=2

// comes from nf-test to store json files
params.nf_test_output  = ""

// include dependencies


// include test workflow
include { AGGREGATE_SUBMISSIONS } from '/scicomp/home-pure/rjd0/tostadas/subworkflows/local/aggregate_submissions.nf'

// define custom rules for JSON that will be generated.
def jsonOutput =
    new JsonGenerator.Options()
        .addConverter(Path) { value -> value.toAbsolutePath().toString() } // Custom converter for Path. Only filename
        .build()

def jsonWorkflowOutput = new JsonGenerator.Options().excludeNulls().build()

workflow {

    // run dependencies
    

    // workflow mapping
    def input = []
    
                input[0] = [ [ batch_id: 'batch_1' ], file("/scicomp/home-pure/rjd0/tostadas/tests/modules/local/fetch_reports/batch_1/") ]
                input[1] = file("/scicomp/home-pure/rjd0/tostadas/conf/submission_config.yaml")
                input[2] = file("/scicomp/home-pure/rjd0/tostadas/tests/subworkflows/local/validated_metadata_all_samples.tsv")
                
    //----

    //run workflow
    AGGREGATE_SUBMISSIONS(*input)
    
    if (AGGREGATE_SUBMISSIONS.output){

        // consumes all named output channels and stores items in a json file
        for (def name in AGGREGATE_SUBMISSIONS.out.getNames()) {
            serializeChannel(name, AGGREGATE_SUBMISSIONS.out.getProperty(name), jsonOutput)
        }	  
    
        // consumes all unnamed output channels and stores items in a json file
        def array = AGGREGATE_SUBMISSIONS.out as Object[]
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
