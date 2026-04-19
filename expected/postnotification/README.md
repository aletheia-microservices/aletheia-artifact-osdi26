# 3. PostNotification

## Summary

| Metric / Pattern | RI-1 | RI-2 | RI-3 | EI-1 | Un-1 |     | Total |
| ---------------- | ---- | ---- | ---- | ---- | ---- | --- | ----- |
| Total Warnings   | 0    | 0    | 1    | 0    | 0    |     | 1     |
| True Positives   | 0    | 0    | 1    | 0    | 0    |     | 1     |
| False Positives  | 0    | 0    | 0    | 0    | 0    |     | 0     |
| False Negatives  | 0    | 0    | 0    | 0    | 0    |     | 0     |

## RI-3: Referential Integrity - Uncoordinated Replication

| #   | Foreign Key Retrieval                   | Foreign Key Usage    | Constraint                                                                          | Foreign Key Retrieval Operation                          | Foreign Key Usage Operation                     |
| --- | --------------------------------------- | -------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------- |
| 1   | notifications_queue.notification.PostID | posts_db.post.PostID | FOREIGN_KEY notifications_queue.notification.PostID REFERENCES posts_db.post.PostID | NotifyService.Run → notifications_queue.notification.Pop | StorageService.ReadPost → posts_db.post.FindOne |
