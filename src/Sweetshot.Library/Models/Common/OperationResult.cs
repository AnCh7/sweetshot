namespace Sweetshot.Library.Models.Common
{
    public class OperationResult
    {
        public bool Success { get; set; }
        public string Error { get; set; }
    }

    public class OperationResult<T> : OperationResult
    {
        public T Result { get; set; }
    }
}