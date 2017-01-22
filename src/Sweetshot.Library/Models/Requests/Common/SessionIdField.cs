using System;
using Newtonsoft.Json;

namespace Sweetshot.Library.Models.Requests.Common
{
    public class SessionIdField
    {
        protected SessionIdField(string sessionId)
        {
            if (string.IsNullOrWhiteSpace(sessionId))
            {
                throw new ArgumentNullException(nameof(sessionId));
            }

            SessionId = sessionId;
        }

        [JsonIgnore]
        public string SessionId { get; private set; }
    }
}