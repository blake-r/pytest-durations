# Note: only simple data types can be used for communication between master and worker xdist processes

FunctionKeyT = str
DurationListT = list[float]
FunctionMeasurementsT = dict[FunctionKeyT, DurationListT]

CategoryT = str
CategoryMeasurementsT = dict[CategoryT, FunctionMeasurementsT]
