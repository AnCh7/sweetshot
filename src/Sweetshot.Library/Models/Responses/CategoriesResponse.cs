using System.Collections.Generic;

namespace Sweetshot.Library.Models.Responses
{
    public class Category
    {
        public string Name { get; set; }
    }

    public class CategoriesResponse
    {
        public List<Category> Results { get; set; }
    }
}