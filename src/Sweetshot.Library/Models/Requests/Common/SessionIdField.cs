namespace Sweetshot.Library.Models.Requests.Common
{
    public class SessionIdField
    {
        protected SessionIdField(string sessionId)
        {
            SessionId = sessionId;
        }

        public string SessionId { get; private set; }
    }
}