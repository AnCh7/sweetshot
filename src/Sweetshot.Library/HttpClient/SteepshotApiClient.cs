using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using Newtonsoft.Json;
using RestSharp;
using Sweetshot.Library.Models.Common;
using Sweetshot.Library.Models.Requests;
using Sweetshot.Library.Models.Responses;
using Sweetshot.Library.Serializing;

namespace Sweetshot.Library.HttpClient
{
    public class SteepshotApiClient
    {
        private const string Url = "http://138.197.40.124/api/v1/";
        private readonly IApiGateway _gateway;
        private readonly IUnmarshaller _unmarshaller;

        public SteepshotApiClient()
        {
            _unmarshaller = new JsonNetUnmarshaller();
            _gateway = new ApiGateway(Url);
        }

        public async Task<OperationResult<LoginResponse>> Login(LoginRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter { Key = "application/json", Value = JsonConvert.SerializeObject(request), Type = ParameterType.RequestBody }
            };

            var response = await _gateway.Post("login", parameters);

            var result = Process<LoginResponse>(response);
            if (result.Success)
            {
                foreach (var cookie in response.Cookies)
                {
                    if (cookie.Name == "sessionid")
                    {
                        result.Result.SessionId = cookie.Value;
                    }
                }

                if (string.IsNullOrEmpty(result.Result.SessionId))
                {
                    result.Success = false;
                    result.Error = "SessionId field is missing";
                }
            }

            return result;
        }

        public async Task<OperationResult<UserPostResponse>> GetUserPosts(UserPostRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie}
            };

            var response = await _gateway.Get($"/user/{request.Username}/posts/", parameters);
            var result = Process<UserPostResponse>(response);
            return result;
        }

        public async Task<OperationResult<UserPostResponse>> GetTopPosts(TopPostRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie},
                new RequestParameter {Key = "Offset", Value = request.Offset, Type = ParameterType.QueryString},
                new RequestParameter {Key = "Limit", Value = request.Limit, Type = ParameterType.QueryString},
                new RequestParameter
                {
                    Key = "application/json",
                    Value = JsonConvert.SerializeObject(request),
                    Type = ParameterType.RequestBody
                }
            };

            var response = await _gateway.Get("posts/top", parameters);
            var result = Process<UserPostResponse>(response);
            return result;
        }

        public async Task<OperationResult<RegisterResponse>> Register(RegisterRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter { Key = "application/json", Value = JsonConvert.SerializeObject(request), Type = ParameterType.RequestBody }
            };

            var response = await _gateway.Post("register", parameters);

            foreach (var cookie in response.Cookies)
                if (cookie.Name == "sessionid")
                {
                }

            return null;
        }

        public async Task<OperationResult<VoteResponse>> UpVote(VoteRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie},
                new RequestParameter
                {
                    Key = "application/json",
                    Value = JsonConvert.SerializeObject(request),
                    Type = ParameterType.RequestBody
                }
            };

            var response = await _gateway.Post($"/post/{request.identifier}/upvote", parameters);
            var result = Process<VoteResponse>(response);
            return result;
        }

        public async Task<OperationResult<VoteResponse>> DownVote(VoteRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie},
                new RequestParameter
                {
                    Key = "application/json",
                    Value = JsonConvert.SerializeObject(request),
                    Type = ParameterType.RequestBody
                }
            };

            var response = await _gateway.Post($"/post/{request.identifier}/downvote", parameters);
            var result = Process<VoteResponse>(response);
            return result;
        }

        public async Task<OperationResult<ImageUploadResponse>> Upload(UploadImageRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie}
            };

            var response = await _gateway.Upload("post", request.title, request.photo, parameters);
            var result = Process<ImageUploadResponse>(response);
            return result;
        }

        public async Task<OperationResult<GetCommentResponse>> GetComments(GetCommentsRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie}
            };

            var response = await _gateway.Get($"/post/{request.url}/comments", parameters);
            var result = Process<GetCommentResponse>(response);
            return result;
        }

        public async Task<OperationResult<CreateCommentResponse>> CreateComment(CreateCommentsRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie},
                new RequestParameter
                {
                    Key = "application/json",
                    Value = JsonConvert.SerializeObject(request),
                    Type = ParameterType.RequestBody
                }
            };

            var response = await _gateway.Post($"/post/{request.url}/comment", parameters);
            var result = Process<CreateCommentResponse>(response);
            return result;
        }

        public async Task<OperationResult<FollowResponse>> Follow(FollowRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie}
            };

            var response = await _gateway.Post($"/user/{request.username}/follow", parameters);
            var result = Process<FollowResponse>(response);
            return result;
        }

        public async Task<OperationResult<FollowResponse>> Unfollow(FollowRequest request)
        {
            var parameters = new List<RequestParameter>
            {
                new RequestParameter {Key = "sessionid", Value = request.SessionId, Type = ParameterType.Cookie}
            };

            var response = await _gateway.Post($"/user/{request.username}/unfollow", parameters);
            var result = Process<FollowResponse>(response);
            return result;
        }

        private OperationResult<T> Process<T>(IRestResponse response)
        {
            var result = new OperationResult<T>();
            var content = response.Content;

            // Network transport or framework errors
            // TODO Check ErrorMessage
            if (response.ErrorException != null)
            {
                result.Error = response.ErrorException.Message;
            }
            // Transport errors
            // TODO Check
            else if (response.ResponseStatus != ResponseStatus.Completed)
            {
                result.Error = "Wrong response status";
            }
            // HTTP errors
            // TODO Check
            else if (response.StatusCode != HttpStatusCode.OK && response.StatusCode != HttpStatusCode.Created)
            {
                result.Error = response.StatusCode.ToString();
            }
            else
            {
                result.Success = true;
            }

            // Parse entity or error
            if (result.Success)
            {
                var entity = _unmarshaller.Process<T>(content);
                result.Result = entity;
            }
            else
            {
                if (string.IsNullOrEmpty(content))
                {
                    result.Error = "Empty response content";
                }
                else if (content.Contains("<html>"))
                {
                    result.Error = content;
                }
                else
                {
                    var error = _unmarshaller.Process<NonFieldError>(content);
                    result.Error = error.Message.First();
                }
            }

            return result;
        }
    }
}