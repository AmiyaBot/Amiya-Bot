const fs = require('fs')
const marked = require('../assets/style/marked.min.js')

const content = fs.readFileSync('function.md').toString()

fs.writeFileSync('md.html', marked.parse(content))
