using Newtonsoft.Json;

namespace Sweetshot.Library.Models.Common
{
    public class NonFieldError
    {
        [JsonProperty(PropertyName = "non_field_errors")]
        public string[] Message { get; set; }
    }
}