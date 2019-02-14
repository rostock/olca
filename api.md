## General parameters

The following parameters are valid for all
requests.

| Name       | Example                                            | Description                                                                                                                                | Required/Default                           |
| ---------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| `query`    | <span class="title-ref">rostock bahnhofsstr</span> | The query string.                                                                                                                          | Yes                                        |
| `type`     | `search`                                           | Type of request, either `search` or `reverse`.                                                                                             | Yes                                        |
| `class`    | <span class="title-ref">address,parcel</span>      | One or more comma-separated classes to search for. Classes are defined in your Geocodr mapping.                                            | Yes                                        |
| `limit`    | <span class="title-ref">20</span>                  | Limit the number of results.                                                                                                               | No. The configured default limit.          |
| `shape`    | `centroid`                                         | One of `geometry` for the original geometry, `centroid` for a single point of the geometry or `bbox` for the bounding box of the geometry. | No. `geometry`                             |
| `out_epsg` | <span class="title-ref">3857</span>                | The EPSG code for the GeoJSON output.                                                                                                      | No. The configured projection of the data. |

`shape=centroid` always returns a point that is
<span class="title-ref">on</span> the polygon or line string g