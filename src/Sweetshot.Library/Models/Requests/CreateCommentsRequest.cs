namespace Sweetshot.Library.Models.Requests
{
    public class CreateCommentsRequest : GetCommentsRequest
    {
        public CreateCommentsRequest(string sessionId, string url, string body, string title) : base(sessionId, url)
        {
            Body = body;
            Title = title;
        }

        public string Body { get; private set; }
        public string Title { get; private set; }
    }
}