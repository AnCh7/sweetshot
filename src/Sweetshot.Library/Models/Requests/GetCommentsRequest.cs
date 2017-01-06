namespace Sweetshot.Library.Models.Requests
{
	public class GetCommentsRequest : SessionIdField
	{
		public GetCommentsRequest(string token, string _url) : base(token)
		{
			url = _url;
		}

		public string url { get; private set; }
	}
}