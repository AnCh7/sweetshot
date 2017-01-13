using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class CategoriesRequest : SessionIdField
    {
        public CategoriesRequest(string sessionId) : base(sessionId)
        {
        }
    }
}