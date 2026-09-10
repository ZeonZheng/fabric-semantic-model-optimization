# SMO Analytics Lakehouse — Data Source Description

SMO Analytics Lakehouse contains current and historical optimization analysis results for Microsoft Fabric and Power BI semantic models.

It provides semantic model inventory and scan status, optimization overviews, prioritized opportunities, implementation recommendations, detailed technical findings and Best Practice Analyzer evidence, as well as VertiPaq table and column storage statistics.

Use this data source to answer questions about:

- which semantic models have been analyzed;
- latest or historical scan status and failures;
- semantic model optimization opportunities and priorities;
- recommended remediation actions, risks, validation, and rollback guidance;
- detailed findings and affected model objects;
- Best Practice Analyzer violations;
- VertiPaq storage, cardinality, and model-size contributors;
- comparisons of optimization results across semantic models or workspaces.

The data source contains both current-state optimization results and historical scan executions. Current-state business tables should be preferred for current optimization analysis, while the analysis-runs table should be used for scan history and troubleshooting.
