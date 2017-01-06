namespace Sweetshot.Library.Models.Requests
{
    public class VoteRequest : SessionIdField
    {
        public VoteRequest(string token, string _identifier) : base(token)
        {
            identifier = _identifier;
        }

        public string identifier { get; private set; }
    }
}