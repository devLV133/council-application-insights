// Authoring dependency: @oai/artifact-tool. The delivered XLSX opens in Excel.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = process.argv[2];
const outputDir = process.argv[3];
if (!root || !outputDir) throw Error('Usage: node build_workbook.mjs REPO_ROOT OUTPUT_DIR');
const data = JSON.parse(await fs.readFile(path.join(root,'data/processed/workbook_data.json'),'utf8'));
await fs.mkdir(outputDir,{recursive:true});
const wb=Workbook.create();
const sheets=Object.fromEntries(['Summary','Applications','Dependencies','Technology'].map(n=>[n,wb.worksheets.add(n)]));
const navy='#172C48', blue='#2563EB', amber='#FFF0CC', ink='#27374A';
function base(s,range){s.showGridLines=false;s.getRange(range).format.font={name:'Arial',size:10,color:ink};s.getRange(range).format.rowHeight=23;}
function header(s,range){s.getRange(range).format={fill:navy,font:{bold:true,color:'#FFFFFF',name:'Arial',size:10},rowHeight:32,wrapText:true,horizontalAlignment:'center',verticalAlignment:'center'};}
function title(s,text){s.getRange('B2').values=[[text]];s.getRange('B2').format.font={name:'Arial',size:16,bold:true,color:navy};}
const s=sheets.Summary; base(s,'B2:M32');title(s,'Council application insights');s.tabColor=navy;
s.getRange('B3').values=[['Synthetic portfolio. Source: project data/raw. Figures as at the reporting date.']];
s.getRange('B4:C4').values=[['Reporting date',new Date(data.summary.as_of_date+'T00:00:00Z')]];
s.getRange('E4:F4').values=[['Review interval (days)',data.summary.stale_days]];
s.getRange('C4').setNumberFormat('dd mmm yyyy');s.getRange('F4').format.fill=amber;
s.getRange('B6:C6').values=[['Portfolio metric','Value']];header(s,'B6:C6');
s.getRange('B7:B14').values=[['Applications'],['Known annual cost (£)'],['Missing annual costs'],['Unowned applications'],['Stale reviews'],['Apps on expired support'],['Apps with quality issues'],['Quality pass rate']];
const n=data.portfolio.length,end=n+6;
s.getRange('C7:C14').formulas=[
 [`=COUNTA(Applications!B7:B${end})`],[`=SUM(Applications!E7:E${end})`],
 [`=SUM(Applications!M7:M${end})`],[`=SUM(Applications!L7:L${end})`],
 [`=SUM(Applications!O7:O${end})`],[`=SUM(Applications!I7:I${end})`],
 [`=COUNTIFS(Applications!R7:R${end},">0")`],['=IF(C7=0,"",(C7-C13)/C7)']];
s.getRange('C8').setNumberFormat('"£"#,##0');s.getRange('C14').setNumberFormat('0.0%');
s.getRange('B17:C17').values=[['Quality rule','Issues']];header(s,'B17:C17');
const issues=[['Missing owner','L'],['Missing cost','M'],['Missing review','N'],['Stale review','O'],['Future review','P'],['No service mapping','Q'],['No technology mapping','K'],['Unknown support date','J']];
s.getRange('B18:B25').values=issues.map(([name])=>[name]);s.getRange('C18:C25').formulas=issues.map(([,c])=>[`=SUM(Applications!${c}7:${c}${end})`]);
s.getRange('B27').values=[['Known costs exclude blank values. Service and technology mappings are SQL snapshots.']];
s.getRange('B28').values=[['Edit owner, cost or review date in Applications to update metrics. Rerun Python for relationship changes.']];
s.getRange('B29').values=[['Reporting date is fixed for this snapshot. Use the Python runner to change it across all outputs.']];
s.getRange('B2:B30').format.columnWidth=29;s.getRange('C2:C30').format.columnWidth=19;s.getRange('D2:D30').format.columnWidth=4;
s.getRange('E2:E30').format.columnWidth=24;s.getRange('F2:M30').format.columnWidth=13;
const chart=s.charts.add('bar',s.getRange('B17:C25'));chart.title='Data quality issues';chart.hasLegend=false;chart.setPosition('E7','M25');
chart.series.items[0].fill=blue;chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=14;
chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:11}};chart.yAxis={numberFormatCode:'0.0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:11}};

const a=sheets.Applications;base(a,`B2:R${end+3}`);title(a,'Application inventory and quality rules');
a.getRange('B3').values=[['Source: synthetic SQL portfolio export. Amber columns are editable inputs. Other input fields are snapshots.']];
a.getRange('B4').values=[['Quality flags are 1 when an issue exists. Scroll right for rule results. Blank annual cost means unknown.']];
a.getRange('B6:R6').values=[['ID','Application','Owner team','Annual cost (£)','Reviewed','Services','Dependent apps','Expired support','Unknown support','No tech mapping','No owner','No cost','No review','Stale review','Future review','No service','Quality issues']];header(a,'B6:R6');
a.getRange(`B7:K${end}`).values=data.portfolio.map(r=>[r.app_id,r.application,r.owner_team,r.annual_cost_gbp,r.last_reviewed?new Date(r.last_reviewed+'T00:00:00Z'):null,r.service_count,r.dependent_apps,r.unsupported_technology,r.unknown_support,r.missing_technology]);
for(let r=7;r<=end;r++)a.getRange(`L${r}:R${r}`).formulas=[[
 `=IF(OR(D${r}="",D${r}="Unassigned"),1,0)`,`=IF(ISBLANK(E${r}),1,0)`,`=IF(ISBLANK(F${r}),1,0)`,
 `=IF(F${r}="",0,IF(F${r}<'Summary'!$C$4-'Summary'!$F$4,1,0))`,
 `=IF(F${r}="",0,IF(F${r}>'Summary'!$C$4,1,0))`,`=IF(G${r}=0,1,0)`,`=SUM(J${r}:Q${r})`]];
a.getRange(`D7:F${end}`).format.fill=amber;a.getRange(`E7:E${end}`).setNumberFormat('"£"#,##0');a.getRange(`F7:F${end}`).setNumberFormat('dd mmm yyyy');
a.getRange(`J7:R${end}`).conditionalFormats.add('cellIs',{operator:'greaterThan',formula:0,format:{fill:'#FDE8E7',font:{color:'#A22724'}}});
a.getRange(`B2:B${end}`).format.columnWidth=8;a.getRange(`C2:D${end}`).format.columnWidth=26;a.getRange(`E2:F${end}`).format.columnWidth=18;a.getRange(`G2:R${end}`).format.columnWidth=13;
a.freezePanes.freezeRows(6);a.freezePanes.freezeColumns(3);

const d=sheets.Dependencies;base(d,'B2:F20');title(d,'Direct application dependencies');d.getRange('B3').values=[['Source: synthetic dependencies export. A row means the application directly depends on the named system.']];
d.getRange('B5:F5').values=[['Application','Depends on','Dependency owner','Expired support','Unknown support']];header(d,'B5:F5');
d.getRange(`B6:F${5+data.dependency_detail.length}`).values=data.dependency_detail.map(r=>[r.application,r.dependency,r.dependency_owner,r.dependency_unsupported,r.dependency_unknown_support]);
d.getRange('B2:D20').format.columnWidth=27;d.getRange('E2:F20').format.columnWidth=18;d.freezePanes.freezeRows(5);
d.getRange('B19').values=[['Direct links only. Counts do not establish outage probability or resilience.']];
const t=sheets.Technology;base(t,'B2:F20');title(t,'Technology lifecycle');t.getRange('B3').values=[['Source: synthetic technology export. End dates are invented, not vendor lifecycle claims.']];
t.getRange('B5:F5').values=[['ID','Technology','Support ends','Applications','Status']];header(t,'B5:F5');
t.getRange(`B6:E${5+data.technology_exposure.length}`).values=data.technology_exposure.map(r=>[r.technology_id,r.technology,r.support_end?new Date(r.support_end+'T00:00:00Z'):null,r.applications]);
for(let r=6;r<6+data.technology_exposure.length;r++)t.getRange(`F${r}`).formulas=[[`=IF(D${r}="","Unknown",IF(D${r}<'Summary'!$C$4,"Expired","Supported"))`]];
t.getRange('B2:B20').format.columnWidth=8;t.getRange('C2:C20').format.columnWidth=34;t.getRange('D2:F20').format.columnWidth=19;t.getRange('D6:D11').setNumberFormat('dd mmm yyyy');
t.getRange('F6:F11').conditionalFormats.add('containsText',{text:'Expired',format:{fill:'#FDE8E7',font:{color:'#A22724'}}});
t.getRange('B14').values=[['Application support flags in the other sheets remain the SQL snapshot until regenerated.']];

wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Summary!B6:C14',include:'values,formulas',tableMaxRows:9,tableMaxCols:2})).ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:30}});
console.log(errors.ndjson);
const v=s.getRange('C7:C14').values.flat();
const st=data.summary;
const expected=[st.applications,st.known_annual_cost_gbp,st.missing_cost_apps,st.unowned_apps,st.stale_reviews,st.unsupported_apps,st.apps_with_quality_issues,st.quality_pass_rate];
if(JSON.stringify(v)!==JSON.stringify(expected))throw Error('Summary reconciliation failed: '+JSON.stringify(v));
// Exercise a real workbook dependency then restore before export.
const blankIndex=data.portfolio.findIndex(r=>r.annual_cost_gbp===null);
if(blankIndex>=0){
 const cell=a.getRange('E'+(blankIndex+7)); const original=cell.values;
 cell.values=[[0]];wb.recalculate();
 if(s.getRange('C9').values[0][0]!==st.missing_cost_apps-1)throw Error('Zero/blank cost check failed');
 cell.values=original;wb.recalculate();
}
for(const [name,range,suffix] of [['Summary','B2:M30','summary'],['Applications',`B2:K${end}`,'applications'],['Applications',`L6:R${end}`,'quality-rules'],['Dependencies','B2:F20','dependencies'],['Technology','B2:F16','technology']]){
 const img=await wb.render({sheetName:name,range,scale:1.5,format:'png'});
 await fs.writeFile(path.join(outputDir,suffix+'.png'),new Uint8Array(await img.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(path.join(outputDir,'Council_Application_Insights.xlsx'));
console.log('Workbook verified and exported.');
