class XmlToJson {
    def static xmlToJson(xmlFile) {
        def xmlSlurper = new XmlSlurper()
        def xmlParsed = xmlSlurper.parse(xmlFile)
        def jsonBuilder = new groovy.json.JsonBuilder(xmlParsed)
        return new groovy.json.JsonSlurper().parseText(jsonBuilder.toString())
    }
}
