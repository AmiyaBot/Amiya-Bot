const record = []
for (let table of document.querySelectorAll('.wikitable.fullline')) {
    for (let img of table.querySelectorAll('img[decoding="async"]')) {
        const src = img.attributes['data-src'].value
        const suffix = img.alt.split('.')[img.alt.split('.').length - 1]
        const name = img.parentNode.parentNode.innerText.replace(/\n/g, '')
        record.push({
            filename: `${name}.${suffix}`,
            url: location.origin + src.split(suffix)[0].replace('/thumb', '') + suffix
        })
    }
}
console.log(JSON.stringify(record))
