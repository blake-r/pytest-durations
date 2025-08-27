# Note: only simple data types can be used for communication between master and worker xdist processes
from pytest_durations.types import Category

FunctionT = str
FunctionMeasurementsT = dict[FunctionT, list[float]]

CategoryMeasurementsT = dict[Category, FunctionMeasurementsT]
