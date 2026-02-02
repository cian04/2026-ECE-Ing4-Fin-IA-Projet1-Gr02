% =========================
% MiniZinc refinement model (Option A)
% Input: fixed matchups per day (pairs), decision is home/away orientation.
% Hard constraints:
%   - unavailable home days
%   - max away streak <= MAX_AWAY
%   - max home streak <= MAX_HOME
%   - home/away balance abs(home-away) <= 1
%   - if 2 consecutive away -> distance between the two away locations <= MAX_CONSEC_AWAY_TRAVEL
% Objective (lexicographic simulated):
%   minimize total_breaks first, then total_distance:
%     obj = total_breaks * BIG + total_distance
% Output: JSON { total_breaks, total_distance, orient }
% =========================

int: D;          % number of days
int: T;          % number of teams
int: M;          % matches per day

int: MAX_AWAY;                 % hard limit consecutive away
int: MAX_HOME;                 % hard limit consecutive home
int: MAX_CONSEC_AWAY_TRAVEL;   % hard constraint for distance between 2 consecutive away locations
int: BIG;                      % weight to enforce breaks priority

array[1..D, 1..M, 1..2] of int: match; % teams are 1..T (unoriented pair)
array[1..T, 1..D] of int: unavailable_home; % 1 means team t cannot be home on day d

array[1..T, 1..T] of int: dist; % dist[i,j] between city i and city j, dist[i,i]=0

% orient[d,m] = 0 -> match[d,m,1] is home
% orient[d,m] = 1 -> match[d,m,2] is home
array[1..D, 1..M] of var 0..1: orient;

% is_home[t,d] = 1 if team t plays home on day d
array[1..T, 1..D] of var 0..1: is_home;

% opponent[t,d] = opponent team id on day d
array[1..T, 1..D] of var 1..T: opponent;

% location[t,d] = city/team id where team t plays on day d
% if home -> t, else -> opponent[t,d]
array[1..T, 1..D] of var 1..T: location;

% ------------------------------------------------------------
% Sanity: each team appears exactly once per day in match data
% ------------------------------------------------------------
constraint forall(t in 1..T, d in 1..D)(
  sum(m in 1..M)( bool2int(match[d,m,1] = t \/ match[d,m,2] = t) ) = 1
);

% ------------------------------------------------------------
% Build is_home from orient
% ------------------------------------------------------------
constraint forall(d in 1..D, m in 1..M)(
  is_home[ match[d,m,1], d ] = 1 - orient[d,m] /\
  is_home[ match[d,m,2], d ] = orient[d,m]
);

% ------------------------------------------------------------
% Build opponent[t,d] from match data
% ------------------------------------------------------------
constraint forall(d in 1..D, m in 1..M)(
  let { int: t1 = match[d,m,1]; int: t2 = match[d,m,2]; } in
    (opponent[t1,d] = t2 /\ opponent[t2,d] = t1)
);

% ------------------------------------------------------------
% Build location[t,d]
% ------------------------------------------------------------
constraint forall(t in 1..T, d in 1..D)(
  location[t,d] = if is_home[t,d] = 1 then t else opponent[t,d] endif
);

% ------------------------------------------------------------
% HARD: Unavailable home days
% ------------------------------------------------------------
constraint forall(t in 1..T, d in 1..D)(
  unavailable_home[t,d] = 1 -> is_home[t,d] = 0
);

% ------------------------------------------------------------
% HARD: Max away streak <= MAX_AWAY (window size MAX_AWAY+1)
% ------------------------------------------------------------
constraint forall(t in 1..T, start in 1..D - MAX_AWAY)(
  sum(d in start..start + MAX_AWAY)(1 - is_home[t,d]) <= MAX_AWAY
);

% ------------------------------------------------------------
% HARD: Max home streak <= MAX_HOME (window size MAX_HOME+1)
% ------------------------------------------------------------
constraint forall(t in 1..T, start in 1..D - MAX_HOME)(
  sum(d in start..start + MAX_HOME)(is_home[t,d]) <= MAX_HOME
);

% ------------------------------------------------------------
% HARD: Home/Away balance abs(home-away) <= 1
% home-away = 2*home_count - D
% ------------------------------------------------------------
constraint forall(t in 1..T)(
  abs(2 * sum(d in 1..D)(is_home[t,d]) - D) <= 1
);

% ------------------------------------------------------------
% HARD: If two consecutive away, enforce not too far between away locations
% ------------------------------------------------------------
constraint forall(t in 1..T, d in 2..D)(
  (is_home[t,d-1] = 0 /\ is_home[t,d] = 0) ->
    dist[ location[t,d-1], location[t,d] ] <= MAX_CONSEC_AWAY_TRAVEL
);

% ------------------------------------------------------------
% Breaks: same H/A as previous day
% ------------------------------------------------------------
array[1..T, 2..D] of var 0..1: br;
constraint forall(t in 1..T, d in 2..D)(
  br[t,d] = bool2int(is_home[t,d] = is_home[t,d-1])
);
var int: total_breaks = sum(t in 1..T, d in 2..D)(br[t,d]);

% ------------------------------------------------------------
% Total travel distance:
% start from home city (t) to day 1 location, then between days
% ------------------------------------------------------------
var int: total_distance =
  sum(t in 1..T)(
    dist[t, location[t,1]] +
    sum(d in 2..D)( dist[ location[t,d-1], location[t,d] ] )
  );

var int: objective = total_breaks * BIG + total_distance;

solve minimize objective;

% Output JSON (single line)
output [
  "{",
  "\"total_breaks\":", show(total_breaks), ",",
  "\"total_distance\":", show(total_distance), ",",
  "\"orient\":[",
    concat([
      if d > 1 then "," else "" endif ++
      "[" ++ concat([
        if m > 1 then "," else "" endif ++ show(orient[d,m])
        | m in 1..M
      ]) ++ "]"
      | d in 1..D
    ]),
  "]",
  "}"
];
