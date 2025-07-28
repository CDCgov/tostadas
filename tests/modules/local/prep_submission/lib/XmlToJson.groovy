class XmlToJson {
    static xmlToJson(xmlFile) {
        def xmlSlurper = new XmlSlurper()
        def xmlParsed = xmlSlurper.parse(xmlFile)
        def jsonStr = groovy.json.JsonOutput.toJson(toMap(xmlParsed))
        return new groovy.json.JsonSlurper().parseText(jsonStr)
    }

    // Recursive function to convert Node to Map
    private static Object toMap(node) {
        if (node instanceof groovy.util.slurpersupport.NodeChild) {
            def map = [:]
            map.putAll(node.attributes())
            node.children().each { child ->
                def name = child.name()
                def value = toMap(child)
                if (map.containsKey(name)) {
                    if (map[name] instanceof List) {
                        map[name] << value
                    } else {
                        map[name] = [ map[name], value ]
                    }
                } else {
                    map[name] = value
                }
            }
            return map.isEmpty() ? node.text() : map
        } else {
            return node.toString()
        }
    }
}
