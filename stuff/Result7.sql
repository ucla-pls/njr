/*All programs with method analysis property of 7*/
SELECT DISTINCT njr_v2.raw_program.name AS program_name FROM njr_v2.method_analysis_property1 
INNER JOIN njr_v2.method ON njr_v2.method_analysis_property1.method_id = njr_v2.method.method_id 
INNER JOIN njr_v2.class ON njr_v2.class.class_id = njr_v2.method.class_id
INNER JOIN njr_v2.raw_program ON njr_v2.raw_program.mainclass_id = njr_v2.method.class_id
WHERE njr_v2.method_analysis_property1.result = 7 
