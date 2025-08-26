# Note: only simple data types can be used for communication between master and worker xdist processes
from pytest_durations.types import Category

FunctionKeyT = str
DurationListT = list[float]
FunctionMeasurementsT = dict[FunctionKeyT, DurationListT]

CategoryMeasurementsT = dict[Category, FunctionMeasurementsT]
