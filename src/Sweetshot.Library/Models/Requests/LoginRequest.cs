using Newtonsoft.Json;

namespace Sweetshot.Library.Models.Requests
{
    public class LoginRequest
    {
        public LoginRequest(string username, string password)
        {
            Username = username;
            Password = password;
        }

        [JsonProperty(PropertyName = "username")]
        public string Username { get; set; }

        [JsonProperty(PropertyName = "password")]
        public string Password { get; set; }
    }
}