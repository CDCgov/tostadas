import groovy.json.JsonGenerator
import groovy.json.JsonGenerator.Converter

nextflow.enable.dsl=2

// comes from nf-test to store json files
params.nf_test_output  = ""

// include dependencies


// include test process
include { BAKTA } from '/scicomp/home-pure/rjd0/tostadas/modules/nf-core/bakta/bakta/main.nf'

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
    
                // todo: need to change the bakta path
                input[0] = file("/scicomp/reference/bakta/bakta/")
                input[1] =  [   [ 
                                batch_id: "batch_1",
                                batch_tsv: file("/scicomp/home-pure/rjd0/tostadas/tests/modules/nf-core/bakta/bakta/batch_1.tsv"),
                                sample_id: "CP040557" 
                                ],
                                file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastas/bacteria/CP040557.fasta"), 
                                file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastqs/bacteria/CP040557_R1.fastq.gz"), 
                                file("/scicomp/home-pure/rjd0/tostadas/assets/sample_fastqs/bacteria/CP040557_R2.fastq.gz") 
                            ]
                
    //----

    //run process
    BAKTA(*input)

    if (BAKTA.output){

        // consumes all named output channels and stores items in a json file
        for (def name in BAKTA.out.getNames()) {
            serializeChannel(name, BAKTA.out.getProperty(name), jsonOutput)
        }	  
      
        // consumes all unnamed output channels and stores items in a json file
        def array = BAKTA.out as Object[]
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
