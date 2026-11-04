"""Build the native PBIP report and TMSL model from the exported column contract."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'powerbi'
BASE = 'https://developer.microsoft.com/json-schemas/'
TABLES = {'Applications':'portfolio', 'Issues':'quality_issues', 'Dependencies':'dependency_detail',
          'Services':'service_exposure', 'Technologies':'technology_exposure', 'Context':'report_context'}
INTS = {'service_count','dependent_apps','missing_owner','missing_cost','missing_review','stale_review',
        'future_review','missing_service','missing_technology','unknown_support','unsupported_technology',
        'dependency_unsupported','dependency_unknown_support','applications','unsupported_apps',
        'unowned_apps','unknown_support_apps','context_id','stale_days'}
DATES = {'last_reviewed','support_end','as_of_date','review_cutoff'}
MEASURES = {
    'Applications': ('COUNTROWS(Applications)', '0'),
    'Known annual cost': ('SUM(Applications[annual_cost_gbp])', '£#,0'),
    'Missing cost': ('SUM(Applications[missing_cost])', '0'),
    'Unowned applications': ('SUM(Applications[missing_owner])', '0'),
    'Unsupported applications': ('SUM(Applications[unsupported_technology])', '0'),
    'Quality issues': ('COALESCE(COUNTROWS(Issues), 0)', '0'),
    'Applications with issues': ('COALESCE(DISTINCTCOUNT(Issues[app_id]), 0)', '0'),
    'Quality pass rate': ('DIVIDE([Applications] - [Applications with issues], [Applications])', '0.0%'),
    'Reporting date': ('MAX(Context[as_of_date])', 'dd MMM yyyy'),
    'Service applications': ('SUM(Services[applications])', '0'),
    'Expired support apps': ('SUM(Services[unsupported_apps])', '0'),
}


def write(path, obj):
    path = OUT/path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n',encoding='utf-8')


def schema(kind, version='1.0.0'):
    return BASE+f'fabric/item/report/definition/{kind}/{version}/schema.json'


def field(table, name, measure=False):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}


def projection(table, name, measure=False, label=None):
    return {'field':field(table,name,measure),'queryRef':table+'.'+name,'nativeQueryRef':name,
            'displayName':label or name.replace('_',' ').capitalize()}


def literal(value):
    return {'expr':{'Literal':{'Value':value}}}


def build():
    write(Path('CouncilInsights.pbip'),{'$schema':BASE+'fabric/pbip/pbipProperties/1.0.0/schema.json',
          'version':'1.0','artifacts':[{'report':{'path':'CouncilInsights.Report'}}],
          'settings':{'enableAutoRecovery':True}})
    write(Path('CouncilInsights.SemanticModel/definition.pbism'),{
        '$schema':BASE+'fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0'})
    model_tables=[]
    for table, filename in TABLES.items():
        with (ROOT/'data/processed'/f'{filename}.csv').open() as f: columns=next(csv.reader(f))
        defs=[];types=[]
        for col in columns:
            datatype,mtype=('int64','Int64.Type') if col in INTS else ('dateTime','type date') if col in DATES else ('decimal','Currency.Type') if col=='annual_cost_gbp' else ('string','type text')
            definition={'name':col,'dataType':datatype,'sourceColumn':col,'summarizeBy':'none'}
            if col in DATES: definition['formatString']='dd MMM yyyy'
            if col=='annual_cost_gbp':definition['formatString']='£#,0'
            defs.append(definition);types.append('{"'+col+'", '+mtype+'}')
        expression=[
            'let',
            f'    Source = Csv.Document(File.Contents(DataFolder & "/{filename}.csv"), [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            '    Blanks = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),',
            '    Types = Table.TransformColumnTypes(Blanks, {'+', '.join(types)+'}, "en-GB")',
            'in','    Types']
        obj={'name':table,'columns':defs,'partitions':[{'name':table,'mode':'import','source':{'type':'m','expression':expression}}]}
        if table=='Applications':obj['measures']=[{'name':n,'expression':e,'formatString':fmt} for n,(e,fmt) in MEASURES.items()]
        model_tables.append(obj)
    model={'name':'CouncilInsights','compatibilityLevel':1550,'model':{
        'culture':'en-GB','defaultPowerBIDataSourceVersion':'powerBI_V3',
        'sourceQueryCulture':'en-GB',
        'expressions':[{'name':'DataFolder','kind':'m','expression':'"C:/council-application-insights/data/processed" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
        'tables':model_tables,'relationships':[
            {'name':'Issues_Applications','fromTable':'Issues','fromColumn':'app_id','toTable':'Applications','toColumn':'app_id','crossFilteringBehavior':'oneDirection'},
            {'name':'Dependencies_Applications','fromTable':'Dependencies','fromColumn':'app_id','toTable':'Applications','toColumn':'app_id','crossFilteringBehavior':'oneDirection'}]}}
    write(Path('CouncilInsights.SemanticModel/model.bim'),model)
    report=Path('CouncilInsights.Report')
    write(report/'definition.pbir',{'$schema':BASE+'fabric/item/report/definitionProperties/2.0.0/schema.json',
          'version':'4.0','datasetReference':{'byPath':{'path':'../CouncilInsights.SemanticModel'}}})
    write(report/'definition/version.json',{'$schema':schema('versionMetadata'),'version':'4.0.0'})
    write(report/'definition/report.json',{'$schema':schema('report','2.0.0'),'themeCollection':{},'reportSource':'Default'})
    pages=['overview','dependencies','quality']
    write(report/'definition/pages/pages.json',{'$schema':schema('pagesMetadata'),'pageOrder':pages,'activePageName':'overview'})
    count=0
    def visual(page,typ,title,x,y,w,h,roles=None,text=None):
        nonlocal count
        count+=1;name=f'visual{count:03}'
        v={'visualType':typ,'visualContainerObjects':{'title':[{'properties':{
            'show':literal('true'),'text':literal("'"+title.replace("'","''")+"'"),
            'fontSize':literal('12D'),'fontColor':{'solid':{'color':literal("'#172C48'")}}}}]},
            'drillFilterOtherVisuals':True}
        if roles:v['query']={'queryState':{role:{'projections':projs} for role,projs in roles.items()}}
        if text:
            v['visualContainerObjects']={}
            v['objects']={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,
                'textStyle':{'fontFamily':'Segoe UI','fontSize':'20pt','color':'#172C48'}}]}]}}]}
        write(report/f'definition/pages/{page}/visuals/{name}/visual.json',{
            '$schema':schema('visualContainer','2.0.0'),'name':name,
            'position':{'x':x,'y':y,'z':count,'width':w,'height':h,'tabOrder':count},'visual':v})
    for p,title in zip(pages,['Portfolio overview','Dependencies and support','Data quality']):
        write(report/f'definition/pages/{p}/page.json',{'$schema':schema('page','2.0.0'),
              'name':p,'displayName':title,'displayOption':'FitToPage','width':1280,'height':800})
        visual(p,'textbox','',30,15,1220,65,text=title+' | Synthetic council portfolio')
    for i,name in enumerate(['Applications','Known annual cost','Missing cost','Unowned applications']):
        visual('overview','card',name,30+i*310,95,295,120,{'Data':[projection('Applications',name,True,name)]})
    visual('overview','clusteredBarChart','Known annual cost by owner (£)',30,235,590,260,{
        'Category':[projection('Applications','owner_team')],'Y':[projection('Applications','Known annual cost',True)]})
    visual('overview','tableEx','Application inventory',645,235,605,500,{'Values':[
        projection('Applications',c) for c in ['application','owner_team','annual_cost_gbp','service_count']]})
    visual('overview','card','Reporting date',30,520,280,100,{'Data':[projection('Applications','Reporting date',True)]})
    visual('overview','textbox','',30,650,590,90,text='Costs exclude unknown values. Shared applications are counted once. Figures are fictional.')
    visual('dependencies','tableEx','Direct application dependencies',30,100,760,320,{'Values':[
        projection('Dependencies',c) for c in ['application','dependency','dependency_owner']]})
    visual('dependencies','tableEx','Technology lifecycle',30,440,760,300,{'Values':[
        projection('Technologies',c) for c in ['technology','support_end','support_status','applications']]})
    visual('dependencies','card','Applications on expired support',820,100,430,120,{'Data':[
        projection('Applications','Unsupported applications',True)]})
    visual('dependencies','tableEx','Service exposure (direct mappings)',820,250,430,490,{'Values':[
        projection('Services',c) for c in ['service','applications','unsupported_apps','unknown_support_apps']]})
    for i,name in enumerate(['Quality issues','Applications with issues','Quality pass rate']):
        visual('quality','card',name,30+i*410,95,390,120,{'Data':[projection('Applications',name,True,name)]})
    visual('quality','tableEx','Issue register and next action',30,240,1220,450,{'Values':[
        projection('Issues',c) for c in ['app_id','application','owner_team','issue','action']]})
    visual('quality','textbox','',30,715,1220,65,text='A record passes when none of the eight quality rules flags an issue. Support expiry is reported separately.')
    print(f'Built 3 report pages and {count} visuals. Desktop verification still required.')


if __name__=='__main__':build()
