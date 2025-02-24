function processRemoteTeleworkData(workbook: ExcelScript.Workbook) {
    const fiscalYearSheet = retrieveWorksheetByName(workbook, "FY2025");
    if (!fiscalYearSheet) {
        console.log("Sheet 'FY2025' not found.");
        return;
    }

    const remoteWorkEntries = extractRemoteTeleworkRows(fiscalYearSheet);
    if (remoteWorkEntries.length < 2) {
        console.log("No matching rows found containing 'remote' or 'telework'.");
        return;
    }

    formatRemoteTeleworkOutput(workbook, remoteWorkEntries);
}


function retrieveWorksheetByName(workbook: ExcelScript.Workbook, sheetName: string): ExcelScript.Worksheet | null {
    try {
        return workbook.getWorksheet(sheetName);
    } catch (error) {
        console.error(`Error retrieving worksheet '${sheetName}': ${error.message}`);
        return null;
    }
}


function extractRemoteTeleworkRows(sourceSheet: ExcelScript.Worksheet): (string | number | boolean | null)[][] {
    const dataRange = sourceSheet.getRange("A:AE").getUsedRange();
    const allValues = dataRange.getValues();
    const filteredRows: (string | number | boolean | null)[][] = [allValues[0]];

    for (let i = 1; i < allValues.length; i++) {
        const row = allValues[i];
        const descriptionCell = row[7];
        if (typeof descriptionCell === "string" && (
            descriptionCell.toLowerCase().includes("remote") ||
            descriptionCell.toLowerCase().includes("telework"))
        ) {
            filteredRows.push(row);
        }
    }
    return filteredRows;
}


function formatRemoteTeleworkOutput(workbook: ExcelScript.Workbook, filteredData: (string | number | boolean | null)[][]) {
    const outputSheet = retrieveOrCreateWorksheet(workbook, "Remote_Telework");
    outputSheet.getRange().clear();

    const dataRange = outputSheet.getRangeByIndexes(0, 0, filteredData.length, filteredData[0].length);
    dataRange.setValues(filteredData);
    outputSheet.getUsedRange()?.getFormat().autofitColumns();

    const table = outputSheet.addTable(dataRange, true);
    table.setName("Filtered_Remote_Telework_Data");

    const dateColumnIndexes = Array.from({ length: 19 }, (_, i) => i + 9).concat([30]);
    for (const columnIndex of dateColumnIndexes) {
        const dateColumnRange = outputSheet.getRangeByIndexes(1, columnIndex, filteredData.length - 1, 1);
        dateColumnRange.setNumberFormatLocal("MM/DD/YYYY");
    }

    const tableRange = table.getRange();
    tableRange.getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.top);
    tableRange.getFormat().setHorizontalAlignment(ExcelScript.HorizontalAlignment.left);
}


function retrieveOrCreateWorksheet(workbook: ExcelScript.Workbook, sheetName: string): ExcelScript.Worksheet {
    return retrieveWorksheetByName(workbook, sheetName) || workbook.addWorksheet(sheetName);
}
