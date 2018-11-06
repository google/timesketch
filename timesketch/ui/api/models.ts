/**
 * These interfaces mirror the API schema defined in
 * {@link https://github.com/google/timesketch/blob/master/timesketch/api/v1/resources.py}
 * The ResourceMixin class defines fields for each type of resource.
 * These are reflected here:
 * "interface Status" corresponds to `ResourceMixin.status_fields`,
 * "interface SearchTemplate" corresponds to `ResourceMixin.searchtemplate_fields`
 * and so on.
 */

type DateTime = string;

export interface Status {
  id: number;
  status: string;
  created_at: DateTime;
  updated_at: DateTime;
}

export interface SearchIndex {
  id: number;
  name: string;
  index_name: string;
  description: string;
  status: Status;
  deleted: boolean;
  created_at: DateTime;
  updated_at: DateTime;
}

export interface Timeline {
  id: number;
  name: string;
  description: string;
  color: string;
  searchindex: SearchIndex;
  deleted: boolean;
  status: Status;
  created_at: DateTime;
  updated_at: DateTime;
}

export interface User {
  username: string;
}

export interface SearchTemplate {
  id: number;
  name: string;
  user: User;
  query_string: string;
  query_filter: string;
  query_dsl: string;
  created_at: DateTime;
  updated_at: DateTime;
}

export interface View {
  id: number;
  name: string;
  user: User;
  query_string: string;
  query_filter: string;
  query_dsl: string;
  searchtemplate: SearchTemplate;
  created_at: DateTime;
  updated_at: DateTime;
}

export interface Sketch {
  id: number;
  name: string;
  description: string;
  user: User;
  timelines: Timeline[];
  active_timelines: Timeline[];
  status: Status;
  created_at: DateTime;
  updated_at: DateTime;
}

export interface Story {
  id: number;
  title: string;
  content: string;
  user: User;
  sketch: Sketch;
  created_at: DateTime;
  updated_at: DateTime;
}

export interface Comment {
  comment: string;
  user: User;
  created_at: DateTime;
  updated_at: DateTime;
}

export interface Label {
  name: string;
  user: User;
  created_at: DateTime;
  updated_at: DateTime;
}
