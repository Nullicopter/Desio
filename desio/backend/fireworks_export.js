/**
 * This is a js file that is run through fireworks to export the pages of a file.
 * It's a template. The code creates a temp js file for each file to export, then
 * runs it in fireworks.
 */

try {

(function(){
    
    function exportPages(inFile, outDir, eid){
        var doc = fw.openDocument(inFile, false, true);
        var count = doc.pagesCount;
        
        //0 twice, cause fireworks has a bug (weird, right?!) in that it will export to
        //a gif unless we switch pages then set the export options. 
        var pages = [];
        for(var i = 0; i < count; i++) pages.push(i);
        pages.push(0);
        
        for(var i in pages){
            doc.changeCurrentPage(pages[i]);
            
            var exportOptions = doc.exportOptions;
            exportOptions.exportFormat = 'PNG';
            exportOptions.colorMode = '24 bit';
            doc.setExportOptions(exportOptions);
            
            var name = doc.pageName;
            
            //no master page output
            if(!(doc.hasMasterPage() && 0 == pages[i]))
                fw.exportPages(doc,"Images","Current",outDir+eid+pages[i]+'.png');
        }
        for(var i = 0; i < 100000; i++){;}
        //fw.closeDocument(doc, false);
        doc.save(true);
        //doc.close(true);
    }
    
    var inp = '${in_file}';
    var outd = '${out_dir}';
    
    exportPages(inp, outd, '${eid}');
})();

} catch (exception) {
	alert([exception, exception.lineNumber, exception.fileName].join("\n"));
}