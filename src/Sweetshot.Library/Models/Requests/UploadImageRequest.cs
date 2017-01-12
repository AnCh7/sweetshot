using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class UploadImageRequest : SessionIdField
    {
        public UploadImageRequest(string sessionId, string title, byte[] photo) : base(sessionId)
        {
            Title = title;
            Photo = photo;
        }

        public string Title { get; private set; }
        public byte[] Photo { get; private set; }
    }
}