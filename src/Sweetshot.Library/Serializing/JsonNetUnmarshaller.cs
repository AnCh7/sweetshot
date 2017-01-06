using Newtonsoft.Json;

namespace Sweetshot.Library.Serializing
{
    public interface IUnmarshaller
    {
        T Process<T>(string response);
    }

    public class JsonNetUnmarshaller : IUnmarshaller
    {
        public T Process<T>(string response)
        {
            return UnmarshalResponse<T>(response);
        }

        private T UnmarshalResponse<T>(string content)
        {
            var response = JsonConvert.DeserializeObject<T>(content);
            return response;
        }
    }
}