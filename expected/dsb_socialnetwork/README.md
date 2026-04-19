# 6. SocialNetwork

## Summary

| Metric / Pattern | RI-1 | RI-2 | RI-3 | EI-1 | Un-1 |     | Total |
| ---------------- | ---- | ---- | ---- | ---- | ---- | --- | ----- |
| Total Warnings   | 0    | 0    | 3    | 0    | 0    |     | 3     |
| True Positives   | 0    | 0    | 3    | 0    | 0    |     | 3     |
| False Positives  | 0    | 0    | 0    | 0    | 0    |     | 0     |
| False Negatives  | 0    | 0    | 0    | 0    | 0    |     | 0     |

## RI-3: Referential Integrity - Uncoordinated Replication

| #   | Foreign Key Retrieval                         | Foreign Key Usage   | Constraint                                                                              | Foreign Key Retrieval Operation                                             | Foreign Key Usage Operation                          |
| --- | --------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | hometimeline_cache.\*.Value[\*].PostID        | post_db.post.PostID | FOREIGN_KEY hometimeline_cache.\*.Value[\*].PostID REFERENCES post_db.post.PostID       | HomeTimelineService.ReadHomeTimeline → hometimeline_cache.\*.Get            | PostStorageService.ReadPosts → post_db.post.FindMany |
| 2   | usertimeline_cache.\*.Value[\*].PostID        | post_db.post.PostID | FOREIGN_KEY usertimeline_cache.\*.Value[\*].PostID REFERENCES post_db.post.PostID       | UserTimelineService.ReadUserTimeline → usertimeline_cache.\*.Get            | PostStorageService.ReadPosts → post_db.post.FindMany |
| 3   | usertimeline_db.usertimeline.Posts[\*].PostID | post_db.post.PostID | FOREIGN_KEY usertimeline_db.usertimeline.Posts[*].PostID REFERENCES post_db.post.PostID | UserTimelineService.ReadUserTimeline → usertimeline_db.usertimeline.FindOne | PostStorageService.ReadPosts → post_db.post.FindMany |
