export interface Team {
  name: string;
  manager: string;
  record: string;
  seed: number;
  pointsFor: number;
  pointsAgainst: number;
}

export interface League {
  name: string;
  season: string;
  teams: number;
}

export interface WeeklyResult {
  week: number;
  result: "W" | "L" | "T";
  score: number;
  oppScore: number;
  opponent: string;
  standing: number;
  event?: string;
}

export interface TradeBreakdown {
  week: number;
  sentPts: number;
  receivedPts: number;
}

export interface PlayerTradeStats {
  player: string;
  ptsROS: number;
  gamesROS: number;
  ppgROS: number;
}

export interface Trade {
  week: number | null;
  partner: string;
  sent: string[];
  received: string[];
  sentPtsROS: number;
  receivedPtsROS: number;
  net: number;
  slotAdjustment?: number;
  sentStats?: PlayerTradeStats[];
  receivedStats?: PlayerTradeStats[];
  weeklyBreakdown: TradeBreakdown[];
}

export interface WaiverWeeklyPoints {
  week: number;
  pts: number;
}

export interface WaiverPickup {
  player: string;
  weekAdded: number | null;
  ptsAfterAdd: number;
  weeklyPoints: WaiverWeeklyPoints[];
}

export interface ScoringCategory {
  total: number;
  pct: number;
}

export type ScoringProfile = Record<string, ScoringCategory>;

export interface AllPlayRecord {
  wins: number;
  losses: number;
  winPct: number;
}

export interface RosterRow {
  slot: string;
  player: string;
  weeks: number[];
}

export interface BenchMisplay {
  week: number;
  benchPlayer: string;
  benchPts: number;
  startPlayer: string;
  startPts: number;
  diff: number;
  wouldHaveWon: boolean;
  lossMargin: number | null;
}

export interface HeadToHeadRecord {
  opponent: string;
  wins: number;
  losses: number;
  playoffWins?: number;
  playoffLosses?: number;
  avgMargin: number;
}

export interface WeeklyLineupComparison {
  week: number;
  actualPts: number;
  optimalPts: number;
  diff: number;
}

export interface OptimalLineup {
  weeklyComparison: WeeklyLineupComparison[];
  totalActual: number;
  totalOptimal: number;
  efficiency: number;
}

export interface Awards {
  mvp?: { player: string; totalPts: number };
  benchWarmer?: {
    player: string;
    weeks: number;
    totalPts: number;
    avgPts: number;
  };
  heartbreakLoss?: {
    week: number;
    opponent: string;
    score: number;
    oppScore: number;
    margin: number;
  };
  statementWin?: {
    week: number;
    opponent: string;
    score: number;
    oppScore: number;
    margin: number;
  };
  luckyWin?: {
    week: number;
    score: number;
    leagueRank: number;
    opponent: string;
    oppScore: number;
  };
  unluckyLoss?: {
    week: number;
    score: number;
    leagueRank: number;
    opponent: string;
    oppScore: number;
  };
}

export interface Grades {
  drafting: string;
  trading: string;
  waiverWire: string;
  luck: string;
  consistency: string;
  overall: string;
}

export interface TeamData {
  team: Team;
  league: League;
  weeklyResults: WeeklyResult[];
  trades: Trade[];
  waiverPickups: WaiverPickup[];
  scoringProfile: ScoringProfile;
  allPlayRecord: AllPlayRecord;
  rosterHeatmap: RosterRow[];
  pointsLeftOnBench: BenchMisplay[];
  headToHead: HeadToHeadRecord[];
  optimalLineup: OptimalLineup;
  awards: Awards;
  grades: Grades;
}

export interface LeagueTeam {
  id: number;
  name: string;
  manager: string;
  record: string;
  standing: number;
  finalPlacement: number;
  pointsFor: number;
  pointsAgainst: number;
}

export interface LeagueTrade {
  week: number | null;
  team1: string;
  team1Id: number;
  team2: string;
  team2Id: number;
  team1Sent: string[];
  team2Sent: string[];
  team1Stats?: PlayerTradeStats[];
  team2Stats?: PlayerTradeStats[];
  team1PtsROS: number;
  team2PtsROS: number;
  net: number;
  winner: string;
  slotAdjustment?: number;
}

export interface DraftPick {
  round: number;
  pick: number;
  overall: number;
  player: string;
  team: string;
  teamId: number;
  seasonPts: number;
  gamesPlayed: number;
  ppg: number;
  adjustedTotal: number;
  seasonRank: number;
  valueOverDraft: number;
  grade: string;
  label: "steal" | "value" | "fair" | "reach" | "bust";
}

export interface DraftMeta {
  replacementFPW: number;
  totalGames: number;
}

export interface DraftTeamGrade {
  team: string;
  grade: string;
  avgValueOverDraft: number;
}

export interface LeaguePickup {
  player: string;
  team: string;
  teamId: number;
  weekAdded: number | null;
  ptsAfterAdd: number;
  gamesPlayed: number;
  ppg: number;
  faabBid: number;
}

export interface LeagueMeta {
  name: string;
  season: string;
  scoringType?: string;
  regSeasonWeeks?: number;
  totalWeeks?: number;
  teams: LeagueTeam[];
  scoringWeights: Record<string, number>;
  leagueAvgScoringProfile: Record<string, number>;
  lineupConfig: Record<string, number>;
  leagueTrades?: LeagueTrade[];
  leaguePickups?: LeaguePickup[];
  draftAnalysis?: DraftPick[];
  draftMeta?: DraftMeta;
  draftGrades?: Record<string, DraftTeamGrade>;
}
