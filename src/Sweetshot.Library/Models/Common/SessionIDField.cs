namespace Sweetshot.Library.Models.Requests
{
    public class SessionIdField
    {
        public SessionIdField(string sessionId)
        {
            SessionId = sessionId;
        }

        public string SessionId { get; private set; }
    }
}