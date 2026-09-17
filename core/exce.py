class DataSageException(Exception):
    pass
class FileParsingError(DataSageException):
    pass
class UnsupportedFileTypeError(DataSageException):
    pass
class CodeExecutionError(DataSageException):
    pass
class DatabaseError(DataSageException):
    pass
class AgentError(DataSageException):
    """Raised when Agent fails"""
    pass