# Resident Advisor GraphQL: Public object types
Based on the live introspection schema of https://ra.co/graphql (schema snapshot 2026-10-18).

Types reachable from event, artist, venue, area, label, promoter, news, search and listing queries.

```graphql
type AdTargeting {
  id: ID!
  userId: Int!
  campaignCode: String!
  targetId: Int!
}

type Address {
  addressLine1: String
  addressLine2: String
  city: String
  stateProvince: String
  country: String
  postalCode: String
}

type AdminUser {
  id: ID!
  username: String
  firstname: String!
  lastname: String!
}

type Aggregation {
  values: [FilterValue]
  type: ListingAggregationType
}

type Area {
  id: ID!
  name: String
  urlName: String
  parentId: ID
  blurb: SecureSanitizedHtml
  population: Int
  ianaTimeZone: String
  country: Country
  parent: Area
  location: GeoLocation
  countryId: Byte!
  isCountry: Boolean!
  subregion: [Area]
  eventsCount: Int!
  venuesCount: Int!
  siblings: [Area]
  guideImageUrl: String
}

type Artist implements IListingItem {
  id: ID!
  countryId: Int
  name: String
  firstName: String
  lastName: String
  areaId: ID
  urlSafeName: String
  bookingDetails: SanitizedHtml
  aliases: StrippedHtml
  pronouns: String
  area: Area
  country: Country
  facebook: String
  instagram: String
  twitter: String
  soundcloud: String
  discogs: String
  bandcamp: String
  website: String
  status: ArtistStatus!
  listingItemId: Int!
  index: IndexType!
  biography: ArtistBio
  residentCountry: Country
  image: String
  coverImage: String
  contentUrl: String
  events(limit: Int, type: EventQueryType!, excludeIds: [ID], year: Int, areaId: Int, country: String): [Event]
  features(limit: Int, excludeIds: [ID], type: FeatureType, dateFrom: DateTime, dateTo: DateTime): [Feature]
  reviews(limit: Int, type: ReviewType, excludeIds: [ID]): [Review]
  news(limit: Int, excludeIds: [ID]): [News]
  exchanges(limit: Int, excludeIds: [ID]): [Exchange]
  podcasts(limit: Int): [Podcast]
  labels(limit: Int, excludeIds: [ID]): [Label]
  followerCount: Int!
  isFollowing: Boolean!
  relatedArtists(limit: Int): [Artist]
  firstEvent: Event
  regionsMostPlayed(limit: Int): [Area]
  venuesMostPlayed(limit: Int): [Venue]
  upcomingEventsCount: Int!
  viewCount: Int!
  soundcloudUser: SoundCloudUser
}

type ArtistBio {
  id: ID!
  blurb: SecureSanitizedHtml
  content: String
  discography: ID
}

type AudioService {
  id: ID!
  name: String!
}

type AuthorizationObjectType {
  assignedPermission(permission: String!): [AuthorizationObjectType]!
  assignedRoles: [Fact]!
  id: ID
  metadata: Metadata
  type: String!
}

type BankAccount implements IPaymentDetails {
  verificationStatus: String!
  type: TransferMethodType!
  bankAccountId: String
  bankAccountPurpose: String
  bankId: String
  bankName: String
  branchId: String
  branchName: String
  branchAddressLine1: String
  branchAddressLine2: String
  branchCity: String
  branchStateProvince: String
  branchPostalCode: String
  branchCountry: String
  firstName: String
  middleName: String
  lastName: String
  addressLine1: String
  addressLine2: String
  city: String
  stateProvince: String
  postalCode: String
  country: String
  countryOfBirth: String
  countryOfNationality: String
  dateOfBirth: String
  employerId: String
  phoneNumber: String
  mobileNumber: String
  driversLicenseId: String
  passportId: String
  governmentId: String
  governmentIdType: String
  businessType: String
  businessName: String
  businessRegistrationId: String
  businessRegistrationStateProvince: String
  businessRegistrationCountry: String
  intermediaryBankAccountId: String
  intermediaryBankAddressLine1: String
  intermediaryBankAddressLine2: String
  intermediaryBankCity: String
  intermediaryBankCountry: String
  intermediaryBankId: String
  intermediaryBankName: String
  intermediaryBankPostalCode: String
  intermediaryBankStateProvince: String
  wireInstructions: String
  token: ID!
  status: String!
  createdOn: DateTime!
  transferMethodCountry: String!
  transferMethodCurrency: String!
}

type Barcode {
  id: ID!
  barcode: Int
  ticketHolder: String
}

type BumpDecision {
  clickUrl: String!  # Click url
  date: LocalDateTime  # Date queried to Kevel in which the bump was returned, can be null for popular events as we query a date range
  eventId: ID!  # Event id
  id: ID!  # Decision bump id
  impressionUrl: String!  # Impression url
  event: Event
}

type BumpDecisionObject {
  bumpDecision: [BumpDecision!]  # Array of bump decisions
}

type BumpsObject {
  budget: Float!
  cpc: Float!
  endDate: DateTime!
  id: ID  # Kevel campaign id
  spend: Float!
  status: BumpStatus!
}

type BumpsValidationObject {
  maximumCpc: Float  # Maximum CPC
  minimumBudget: Float  # Minimum budget
  minimumCpc: Float  # Minimum CPC
}

type Cart {
  id: ID!
  datePurchased: DateTime
  comments: [CartComment]
  cartItems: [CartItem]
}

type CartComment {
  id: ID!
  comment: StrippedHtml!
  dateCreated: DateTime!
}

type CartItem {
  id: ID!
  quantity: Int!
  promoId: Int
  refund: Int!
  ticket: Ticket
  barcodes: [Barcode]
}

type Country {
  id: ID!
  name: String
  urlCode: String
  isoCode: String
  topCountry: Boolean!
  order: Int
  ticketsEnabled: Boolean!
  currency: Currency
  areas: [Area]
  requiresCookieConsent: Boolean!
}

type CreatedFact {
  expiry: DateTime
  resource: AuthorizationObjectType!
  role: String!
  subject: AuthorizationObjectType!
}

type Currency {
  id: ID!
  title: String
  code: String
  symbol: String
  exponent: Int
  bumps: BumpsValidationObject
}

type Email {
  email: String!
}

type Event implements IListingItem {
  id: ID!
  title: String
  date: LocalDateTime!
  startTime: LocalDateTime!
  endTime: LocalDateTime!
  time: String
  cost: StrippedHtml
  isFestival: Boolean
  dateUpdated: DateTime
  content: String
  minimumAge: Int
  isTicketed: Boolean
  hideFromListings: Boolean
  index: IndexType!
  live: Boolean!
  newEventForm: Boolean!
  datePosted: DateTime
  dateCreated: DateTime
  submissionSource: EventSubmissionSource
  ticketFeeType: TicketFeeType
  approvalStatus: ApprovalStatusType
  visibility: VisibilityType
  ticketingSystem: TicketingSystem
  area: Area
  country: Country
  flyerFront: String
  flyerBack: String
  embargoDate: LocalDateTime
  listingItemId: Int!
  autoApproved: Boolean!
  venue: Venue
  pick: EventPick
  promotionalLinks: [PromotionalLink]
  isInterested: Boolean!
  isSaved: Boolean!
  contentUrl: String
  tracking(types: [TrackingType!]): [Tracking]
  userTicketsCount: Int!
  admin: User
  tickets(queryType: EventTicketsQueryType, ticketTierType: TicketTierType): [Ticket]
  viewCount: Int!
  resaleActive: Boolean!
  userOrders: [Order]
  isMultiDayEvent: Boolean!
  queueItEnabled: Boolean!
  status: EventStatus!
  revisions(statuses: [EventRevisionApprovedStatusType!]): [EventRevision]
  availableTicketFeeTypes: [TicketFeeType!]
  totalRevenue: Decimal!
  totalTicketsSold: Int!
  totalTicketAllocation: Int!
  totalPossibleRevenue: Decimal!
  totalTicketsInResale: Int!
  totalTicketsSoldInResale: Int!
  additionalRevenueFromResale: Decimal!
  totalServiceFeeDiscount: Decimal!
  promotersToBePaid: [Promoter]
  promoterRoles: [PromoterRoles]
  canSubscribeToTicketNotifications: Boolean!  # Indicates whether the user can subscribe to ticket notifications for a legacy event. For SHIFT events use Ticketing_Even
  canSendTicketNotifications: Boolean!
  hasPromotersSet: Boolean!
  ticketNotificationSubscriptionsCount: Int
  attending: Int!
  interestedCount: Int!
  images: [EventImage]
  artists(orderBy: EventArtistsOrderByType): [Artist]
  excludedArtists: [Artist]
  lineup: String
  promoters: [Promoter]
  genres: [Genre]
  playerLinks: [PlayerLink]
  childEvents: [Event]
  secretVenueReveal: SecretVenueReveal
  setTimes: SetTimesDto
  hasSecretVenue: Boolean!
  queues: [EventQueue]
  ticketing: Ticketing_Event
  presale: Presale
  isSignedUpToPresale: Boolean
  presaleStatus: PresaleStatus
  guestlist(page: Int!, pageSize: Int!): GuestlistDto
  dashboard(dashboard: String): Embeddable_Token
}

type EventArtistDto {
  artistId: Int!
  eventId: Int!
}

type EventImage {
  id: ID!
  alt: String
  type: ImageType
  filename: String
  crop: Any
}

type EventListing {
  id: ID!
  listingDate: LocalDateTime!
  event: Event
}

type EventListingBumpDecision {
  bumpDecision: [BumpDecision!]  # Array of bump decisions
}

type EventListings {
  data: [EventListing]
  totalResults: Int
  filterOptions: FilterOptions
}

type EventListingsWithBumps {
  eventListings: EventListings
  bumps: EventListingBumpDecision
}

type EventPick {
  id: ID!
  blurb: SecureSanitizedHtml
  author: User
}

type EventQueue {
  id: ID!
  displayName: String
  startTime: DateTime
  endTime: DateTime
  protectedUrl: String
}

type EventRevision {
  id: ID!
  status: EventRevisionApprovedStatusType!
  versionDate: DateTime!
  event: EventRevisionEvent
  user: EventRevisionUser
  userApproved: EventRevisionUser
}

type EventRevisionEvent implements IListingItem {
  id: ID!
  title: String
  date: LocalDateTime!
  startTime: LocalDateTime
  endTime: LocalDateTime
  time: String
  cost: StrippedHtml
  isFestival: Boolean
  dateUpdated: DateTime
  content: String
  minimumAge: Int
  isTicketed: Boolean
  embargoDate: LocalDateTime
  hideFromListings: Boolean
  index: IndexType!
  live: Boolean!
  newEventForm: Boolean!
  visibility: VisibilityType
  area: Area
  country: Country
  artists: [Artist]
  eventPromoters: [RevisionEventPromoterDto]
  images: [EventImage]
  playerLinks: [PlayerLink]
  eventGenres: [RevisionEventGenreDto]
  flyerFront: String
  flyerBack: String
  listingItemId: Int!
  datePosted: DateTime
  dateCreated: DateTime
  submissionSource: EventSubmissionSource!
  autoApproved: Boolean!
  ticketFeeType: TicketFeeType!
  approvalStatus: ApprovalStatusType!
  ticketingSystem: TicketingSystem!
  venue: Venue
  pick: EventPick
  promotionalLinks: [PromotionalLink]
  isInterested: Boolean!
  isSaved: Boolean!
  contentUrl: String
  tracking(types: [TrackingType!]): [Tracking]
  userTicketsCount: Int!
  admin: User
  tickets(queryType: EventTicketsQueryType, ticketTierType: TicketTierType): [Ticket]
  viewCount: Int!
  resaleActive: Boolean!
  userOrders: [Order]
  isMultiDayEvent: Boolean!
  queueItEnabled: Boolean!
  status: EventStatus!
  revisions(statuses: [EventRevisionApprovedStatusType!]): [EventRevision]
  availableTicketFeeTypes: [TicketFeeType!]
  totalRevenue: Decimal!
  totalTicketsSold: Int!
  totalTicketAllocation: Int!
  totalPossibleRevenue: Decimal!
  totalTicketsInResale: Int!
  totalTicketsSoldInResale: Int!
  additionalRevenueFromResale: Decimal!
  totalServiceFeeDiscount: Decimal!
  promotersToBePaid: [Promoter]
  promoterRoles: [PromoterRoles]
  canSubscribeToTicketNotifications: Boolean!  # Indicates whether the user can subscribe to ticket notifications for a legacy event. For SHIFT events use Ticketing_Even
  canSendTicketNotifications: Boolean!
  hasPromotersSet: Boolean!
  ticketNotificationSubscriptionsCount: Int
  attending: Int!
  interestedCount: Int!
  lineup: String
  promoters: [Promoter]
  genres: [Genre]
}

type EventRevisionUser {
  id: ID!
  username: String
}

type EventTypeFilterOption {
  value: Int!
  count: Long!
}

type Exchange {
  id: ID!
  date: DateTime
  title: String
  blurb: SecureSanitizedHtml
  content: SanitizedHtml
  fileSize: Int
  duration: String
  streamingUrl: String
  keywords: String
  tracklist: SanitizedHtml
  isTheHour: Boolean
  imageUrl: String
  contentUrl: String
  artist: Artist
}

type FacetedSearch {
  results: [FacetedSearchResult]
  totalResults: Int
  filterOptions: FilterOptions
}

type FacetedSearchResult {
  id: ID
  data: IListingItem
}

type Fact {
  resource: AuthorizationObjectType!
  role: String!
  subject: AuthorizationObjectType!
}

type Feature implements IListingItem {
  id: ID!
  date: DateTime
  title: String
  blurb: SecureSanitizedHtml
  featured: Boolean!
  photoCredit: SanitizedHtml
  backgroundColor: String
  linkColor: String
  textColor: String
  type: FeatureType
  locale: Locale!
  tech: Boolean
  author: User
  content: String
  youtubeId: String
  imageUrl: String
  imageListing: String
  listingItemId: Int!
  index: IndexType!
  images(type: FeatureHeaderImageType): [FeatureHeaderImage]
  contentUrl: String
  series: FeatureSeries
  artists: [Artist]
  imageListingUrl: String
  localised: [Feature]
}

type FeatureHeaderImage {
  featureId: ID!
  type: FeatureHeaderImageType!
  imageUrl: String
}

type FeatureSeries {
  id: ID!
  title: String
  blurb: SecureSanitizedHtml
  seriesRef: String
  imageUrl: String
  contentUrl: String
  features(limit: Int): [Feature]
}

type FilterOptions {
  genre: [GenreFilterOption]
  eventType: [EventTypeFilterOption]
  location: [LocationFilterOption]
}

type FilterValue {
  name: String!
  value: String!
}

type GenderDto {
  id: ID!
  reference: String!
  name: String!
  dropdownRank: Int
}

type Genre {
  id: ID!
  name: String
  slug: String!
  contentUrl: String
}

type GenreFilterOption {
  value: String!
  count: Long!
  label: String
}

type GeoLocation {
  latitude: Float
  longitude: Float
}

type GroupedEvents {
  date: LocalDateTime!
  events: [Event]
}

type GuestDto {
  allocation: Int!  # The allocation of the guestlist guest
  email: String  # The email of the guestlist guest
  eventId: ID!  # The Event ID of the event that the guestlist guest is for
  id: ID!
  name: String!  # The name of the guestlist guest
}

type I18NLocale {
  id: ID!
  created_at: DateTime!
  updated_at: DateTime!
  name: String
  code: String
}

interface IListingItem {
  index: IndexType!
}

type IPSItem {
  id: ID!
  title: String
  blurb: String
  contentUrl: String
  datePosted: DateTime!
  language: Language
  textColor: IPSItemColor
  imageUrl: String
  imageUrlMobile: String
}

interface IPaymentDetails {
  token: ID!
  status: String!
  type: TransferMethodType!
  createdOn: DateTime!
  transferMethodCountry: String!
  transferMethodCurrency: String!
}

type Invoice {
  id: ID!
  invoiceNumber: String!
  periodStartDate: DateTime!
  country: Country
  currency: Currency
  promoterId: Int!
  periodEndDate: DateTime!
  invoiceDate: DateTime!
  countryId: Byte!
  currencyId: Byte!
  lineItems: [InvoiceLineItem]
}

type InvoiceLineItem {
  id: ID!
  feeType: String!
  feeValue: Decimal!
  invoiceNumber: String
}

type IterableMessageTypeDto {
  id: ID!
  messageTypeId: Int!
  communicationId: Int!
}

type Label implements IListingItem {
  id: ID!
  name: String
  imageLarge: String
  blurb: SecureSanitizedHtml
  live: Boolean
  dateEstablished: String
  link: String
  discogs: String
  facebook: String
  twitter: String
  soundcloud: String
  area: Area
  listingItemId: Int!
  index: IndexType!
  imageUrl: String
  contentUrl: String
  reviews(limit: Int, excludeIds: [ID]): [Review]
  followerCount: Int!
  artists(excludeIds: [ID], limit: Int): [Artist]
  isFollowing: Boolean!
}

type Listing {
  aggregations: [Aggregation]
  totalResults: Int
  data: [IListingItem]
}

type ListingItem {
  id: ID!
  index: IndexType!
}

type LocaleDto {
  id: ID!
  ref: String!
  title: String!
  localTitle: String
}

type LocationFilterOption {
  value: LocationFilterOptionDistanceRange!
  count: Long!
}

type LocationFilterOptionDistanceRange {
  from: Decimal!
  to: Decimal!
}

type ManagedEventListings {
  data: [Event]!
  totalResults: Int!
}

type MarketingCommunicationDto {
  id: ID!
  reference: String!
  iterableMessageType: IterableMessageTypeDto
}

type MergedOrder {
  event: Event
  legacyOrders: [Order]
  ticketingOrders: [Ticketing_Order]
}

type Metadata {
  email: String
}

type MetadataOverride {
  id: ID!
  created_at: DateTime!
  updated_at: DateTime!
  title: String
  description: String
  url: String!
  published_at: DateTime
}

type MetadataOverrideAggregator {
  count: Int
  totalCount: Int
}

type MetadataOverrideConnection {
  values: [MetadataOverride]
  groupBy: MetadataOverrideGroupBy
  aggregate: MetadataOverrideAggregator
}

type MetadataOverrideConnectionCreated_at {
  key: DateTime
  connection: MetadataOverrideConnection
}

type MetadataOverrideConnectionDescription {
  key: String
  connection: MetadataOverrideConnection
}

type MetadataOverrideConnectionId {
  key: ID
  connection: MetadataOverrideConnection
}

type MetadataOverrideConnectionPublished_at {
  key: DateTime
  connection: MetadataOverrideConnection
}

type MetadataOverrideConnectionTitle {
  key: String
  connection: MetadataOverrideConnection
}

type MetadataOverrideConnectionUpdated_at {
  key: DateTime
  connection: MetadataOverrideConnection
}

type MetadataOverrideConnectionUrl {
  key: String
  connection: MetadataOverrideConnection
}

type MetadataOverrideGroupBy {
  id: [MetadataOverrideConnectionId]
  created_at: [MetadataOverrideConnectionCreated_at]
  updated_at: [MetadataOverrideConnectionUpdated_at]
  title: [MetadataOverrideConnectionTitle]
  description: [MetadataOverrideConnectionDescription]
  url: [MetadataOverrideConnectionUrl]
  published_at: [MetadataOverrideConnectionPublished_at]
}

type Microsite {
  title: String
  subNavType: String
  contentUrl: String
  feature(preferredLocale: String, fallbackLocale: String): Feature
}

type News implements IListingItem {
  id: ID!
  headline: Boolean!
  content: SanitizedHtml
  live: Boolean!
  date: DateTime!
  title: String
  blurb: SecureSanitizedHtml
  language: Language
  linkName: String
  link: String
  artist: Artist
  country: Country
  imageUrl: String
  areaId: Int!
  listingItemId: Int!
  index: IndexType!
  contentUrl: String
  author: User
  events: [Event]
  playerLinks: [PlayerLink]
  type: NewsType
  localised: [News]
}

type Order {
  id: ID!
  rAOrderNumber: String
  billingName: String
  currency: Currency
  quantity: Int!
  total: Decimal!
  cart: Cart
}

type PayPalAccount implements IPaymentDetails {
  type: TransferMethodType!
  email: String!
  token: ID!
  status: String!
  createdOn: DateTime!
  transferMethodCountry: String!
  transferMethodCurrency: String!
}

type PlayerLink {
  id: ID!
  sourceId: String!
  audioService: AudioService
}

type Podcast {
  id: ID!
  date: DateTime
  title: String
  live: String!
  fileSize: Int
  duration: String
  keywords: String
  tracklist: SanitizedHtml
  archived: Boolean!
  content: SanitizedHtml
  blurb: String
  imageUrl: String
  streamingUrl: String
  translation: PodcastContent
  contentUrl: String
  artist: Artist
}

type PodcastContent {
  blurb: String
  content: SanitizedHtml
  podcastId: Int!
  language: Language!
}

type ProfileManager {
  hasArtists: Boolean!
  hasPromoters: Boolean!
  hasLabels: Boolean!
}

type Promoter implements IListingItem {
  id: ID!
  name: String
  blurb: SecureSanitizedHtml
  isFestival: Boolean!
  live: Boolean!
  hasCover: Boolean!
  hasTicketAccess: Boolean!
  venueId: ID
  country: Country
  paymentExclusionType: PaymentExclusionType
  area: Area
  website: String
  facebook: String
  instagram: String
  twitter: String
  youtube: String
  logoLarge: String
  imageFeature: String
  areaId: Short!
  termsAgreement: Boolean!
  listingItemId: Int!
  index: IndexType!
  email: String
  coverUrl: String
  logoUrl: String
  contentUrl: String
  news(limit: Int): [News]
  invoices(year: Int, invoiceNumbers: [String]): [Invoice]
  events(limit: Int, type: EventQueryType!, year: Int): [Event]
  followerCount: Int!
  tracking(types: [TrackingType!]): [PromoterTracking]
  upcomingEventsCount: Int!
  isFollowing: Boolean!
  user: User
  features: [PromoterFeatureType!]
  socialMediaLinks: [SocialMediaLink]
  vatNumber: String
}

type PromoterContactPermission {
  id: ID!
  dateAccepted: DateTime
  promoter: Promoter
}

type PromoterRoles {
  id: ID!
  promoterId: ID!
  eventPromoterRole: EventRole
}

type PromoterTracking {
  id: ID!
  code: String
  name: String!
  event: String!
  authToken: String
}

type PromoterTrackingEntry {
  id: Int!
  promoterId: Int!
  type: TemplateType!
  code: String
  authToken: String
}

type PromotionalLink {
  title: String
  url: String
}

type PushNotification {
  id: ID
  title: String
  app: App
  isSubscribed: Boolean!
}

type RecommendedProfiles {
  data: [Artist]
}

type RegisteredUserDto {
  id: Int!
  username: String
  email: String
  areaId: Short!
}

type Review implements IListingItem {
  id: ID!
  language: Language!
  live: Boolean!
  date: DateTime!
  title: String
  blurb: SecureSanitizedHtml
  content: SanitizedHtml
  tracklist: StrippedHtml
  player: SanitizedHtml
  label: String
  releaseDate: String
  type: ReviewType
  recommended: Boolean
  catalogue: String
  author: User
  listingItemId: Int!
  index: IndexType!
  contentUrl: String
  imageUrl: String
  labels: [Label]
  genres: [Genre]
  event: Event
  artists: [Artist]
  playerLinks: [PlayerLink]
  localised: [Review]
  next(limit: Int, types: [ReviewType!]): [Review]
  previous(limit: Int, types: [ReviewType!]): [Review]
}

type RevisionEventArtistDto {
  artistId: Int!
}

type RevisionEventGenreDto {
  genreId: Int!
}

type RevisionEventImageDto {
  image: RevisionImageDto
  type: ImageType!
}

type RevisionEventPlayerLinkDto {
  playerLink: RevisionPlayerLinkDto
}

type RevisionEventPromoterDto {
  promoterId: Int!
}

type RevisionImageDto {
  filename: String
  alt: String
  crop: String
}

type RevisionPlayerLinkDto {
  id: Int!
  sourceId: String
  type: Int!
}

type Search {
  id: ID!
  value: String
  areaName: String
  countryId: Int
  countryName: String
  countryCode: String
  score: Decimal
  contentUrl: String
  imageUrl: String
  searchType: GlobalSearchType
  date: LocalDateTime
  reviewType: ReviewType
  year: Int
  clubName: String
  clubContentUrl: String
}

type SecretVenueReveal {
  revealDate: LocalDateTime
  eventId: Int!
  message: String
  emailOnSubmit: Boolean!
}

type SetTimesDto {
  status: SetTimesStatusType!
  lineup: String
  id: Int
}

type ShareCount {
  id: ID!
  facebook: Int!
}

type SocialMediaLink {
  id: ID!
  platform: SocialMediaPlatformType!
  link: String!
}

type SoundCloudPlaylist {
  id: ID!
  title: String!
  description: String
  urn: String!
  genre: String
  tags: String
  artworkUrl: String
  likesCount: Int
  releaseDay: Int
  releaseMonth: Int
  releaseYear: Int
  trackCount: Int!
  tracks: [SoundCloudTrack!]!
}

type SoundCloudTrack {
  id: ID!
  title: String!
  description: String
  uri: String!
  urn: String!
  genre: String
  duration: Int!
  playbackCount: Int
  likesCount: Int
  artworkUrl: String
  streamUrl: String
  waveformUrl: String
  releaseDay: Int
  releaseMonth: Int
  releaseYear: Int
  metadataArtist: String
  tags: String
}

type SoundCloudUser {
  id: ID!
  username: String!
  followerCount: Int!
  tracks: [SoundCloudTrack]
}

type SourceArtist {
  areas: [SourceArtistArea!]!
  bookingsIncreasePercentage: Float
  contentUrl: String!
  followerCount: Int!
  followerIncreasePercentage: Float
  genres: [SourceArtistGenre!]!
  id: ID!
  imageUrl: String!
  isSaved: Boolean!
  name: String!
  popularBy: SourceArtistPopularBy!
  raMixOfTheDay: Boolean!
  raPickEvent: Boolean!
  raPicksCount: Int!
  raPodcast: Boolean!
  totalEvents: Int!
  upcomingEvents: Int!
}

type SourceArtistArea {
  country: SourceArtistCountry!
  id: ID!
  name: String!
}

type SourceArtistCountry {
  code: String!
  id: ID!
  name: String!
}

type SourceArtistGenre {
  id: ID!
  name: String!
  slug: String!
}

type SourceArtistPopularBy {
  ageRange: [String!]
  gender: [String!]
}

type SourceRecommendation {
  artist: SourceArtist!
  id: ID!
  ticketBuyerFollowerCount: Int!
}

type SourceSavedArtist {
  artist: SourceArtist!
  dateUpdated: DateTime!
  userId: String!
}

type SourceSavedArtistCountAggregate {
  _all: Int!
  dateUpdated: Int!
  userId: Int!
}

type SourceSavedArtistList {
  areaId: String!
  countryId: String!
  date: DateTime
  dateCreated: DateTime!
  dateUpdated: DateTime!
  genres: [SourceSavedArtistListGenre!]
  ianaTimeZone: String!
  id: ID!
  imageUrl: String
  latitude: Float
  longitude: Float
  name: String!
  savedArtistList_savedArtists(distinct: [SourceSavedArtist_SavedArtistListScalarFieldEnum!], orderBy: [SourceSavedArtist_SavedArtistListOrderByWithRelationInput!], skip: Int, take: Int): [SourceSavedArtist_SavedArtistList!]
  savedArtistsCount: Int!
  suggestedArtists(input: SourceSearchInput!, type: SuggestedArtistsType!): SourceSearchResult
}

type SourceSavedArtistListAvgAggregate {
  latitude: Float
  longitude: Float
}

type SourceSavedArtistListCountAggregate {
  _all: Int!
  areaId: Int!
  countryId: Int!
  date: Int!
  dateCreated: Int!
  dateUpdated: Int!
  ianaTimeZone: Int!
  id: Int!
  latitude: Int!
  longitude: Int!
  name: Int!
}

type SourceSavedArtistListGenre {
  listId: String!
  slug: String!
}

type SourceSavedArtistListGenreCountAggregate {
  _all: Int!
  listId: Int!
  slug: Int!
}

type SourceSavedArtistListGenreMaxAggregate {
  listId: String
  slug: String
}

type SourceSavedArtistListGenreMinAggregate {
  listId: String
  slug: String
}

type SourceSavedArtistListMaxAggregate {
  areaId: String
  countryId: String
  date: DateTime
  dateCreated: DateTime
  dateUpdated: DateTime
  ianaTimeZone: String
  id: String
  latitude: Float
  longitude: Float
  name: String
}

type SourceSavedArtistListMinAggregate {
  areaId: String
  countryId: String
  date: DateTime
  dateCreated: DateTime
  dateUpdated: DateTime
  ianaTimeZone: String
  id: String
  latitude: Float
  longitude: Float
  name: String
}

type SourceSavedArtistListSumAggregate {
  latitude: Float
  longitude: Float
}

type SourceSavedArtistMaxAggregate {
  dateUpdated: DateTime
  userId: String
}

type SourceSavedArtistMinAggregate {
  dateUpdated: DateTime
  userId: String
}

type SourceSavedArtist_SavedArtistList {
  agentFee: Float
  artistId: String!
  bookingFee: Float
  dateCreated: DateTime!
  dateUpdated: DateTime
  hasNoEvent: Boolean!
  id: String!
  isBooked: Boolean!
  isLocal: Boolean!
  isNearby: Boolean!
  notes: String
  savedArtist: SourceSavedArtist!
  status: SavedArtistListArtistStatus
  travelFee: Float
}

type SourceSavedArtist_SavedArtistListAvgAggregate {
  agentFee: Float
  bookingFee: Float
  travelFee: Float
}

type SourceSavedArtist_SavedArtistListCountAggregate {
  _all: Int!
  agentFee: Int!
  artistId: Int!
  bookingFee: Int!
  dateCreated: Int!
  dateUpdated: Int!
  notes: Int!
  status: Int!
  travelFee: Int!
}

type SourceSavedArtist_SavedArtistListMaxAggregate {
  agentFee: Float
  artistId: String
  bookingFee: Float
  dateCreated: DateTime
  dateUpdated: DateTime
  notes: String
  status: SavedArtistListArtistStatus
  travelFee: Float
}

type SourceSavedArtist_SavedArtistListMinAggregate {
  agentFee: Float
  artistId: String
  bookingFee: Float
  dateCreated: DateTime
  dateUpdated: DateTime
  notes: String
  status: SavedArtistListArtistStatus
  travelFee: Float
}

type SourceSavedArtist_SavedArtistListSumAggregate {
  agentFee: Float
  bookingFee: Float
  travelFee: Float
}

type SourceSearchFilterOptions {
  area: [SourceSearchTermFilterOption!]!
  bookingsIncreasePercentage: [SourceSearchRangeFilterOption!]!
  followerCount: [SourceSearchRangeFilterOption!]!
  popularByAgeRange: [SourceSearchTermFilterOption!]!
  popularByArea: [SourceSearchTermFilterOption!]!
  totalEvents: [SourceSearchRangeFilterOption!]!
  upcomingEvents: [SourceSearchRangeFilterOption!]!
}

type SourceSearchRangeFilterOption {
  count: Int!
  value: SourceSearchRangeFilterOptionValue!
}

type SourceSearchRangeFilterOptionValue {
  gt: Float
  gte: Float
  lt: Float
  lte: Float
}

type SourceSearchResult {
  data: [SourceArtist!]!
  filterOptions: SourceSearchFilterOptions!
  totalResults: Int!
}

type SourceSearchTermFilterOption {
  count: Int!
  value: String!
}

type TaggedLineup {
  lineup: String
  artists: [Artist]
}

type Ticket {
  id: ID!
  title: String
  priceRetail: Decimal
  dateCreated: DateTime
  visible: Boolean
  validType: TicketValidType
  priceWholesale: Decimal
  totalAllocated: Int
  totalSold: Int
  totalPendingResale: Int!
  status: TicketTierStatus
  resaleQueueEnabled: Boolean
  currency: Currency
  dependency: Ticket
  onSaleFrom: DateTime
  onSaleUntil: DateTime!
  totalReserved: Int!
  resellAsTicketTypeId: Int
  bookingFee: Decimal!
  isAddOn: Boolean!
  totalRevenue: Decimal
  totalPossibleRevenue: Decimal
  event: Event
  depositDependency: Ticket
  isStoppedSales: Boolean!
}

type TicketNotificationSubscriptionsResponse {
  subscriptions: [TicketNotificationsSubscription!]!
  totalCount: Float!
}

type TicketNotificationsSubscription {
  dateUpdated: DateTime!
  eventId: Float!
  type: TicketNotificationSubscriptionType!
  userId: Float!
}

type Track {
  id: ID!
  title: String
}

type Tracking {
  id: ID!
  code: String
  name: String!
  event: String!
}

type UploadFile {
  id: ID!
  created_at: DateTime!
  updated_at: DateTime!
  name: String!
  alternativeText: String
  caption: String
  width: Int
  height: Int
  formats: JSON
  hash: String!
  ext: String
  mime: String!
  size: Float!
  url: String!
  previewUrl: String
  provider: String!
  provider_metadata: JSON
  related(sort: String, limit: Int, start: Int, where: JSON): [Morph]
}

type UploadFileAggregator {
  count: Int
  totalCount: Int
  sum: UploadFileAggregatorSum
  avg: UploadFileAggregatorAvg
  min: UploadFileAggregatorMin
  max: UploadFileAggregatorMax
}

type UploadFileAggregatorAvg {
  width: Float
  height: Float
  size: Float
}

type UploadFileAggregatorMax {
  width: Float
  height: Float
  size: Float
}

type UploadFileAggregatorMin {
  width: Float
  height: Float
  size: Float
}

type UploadFileAggregatorSum {
  width: Float
  height: Float
  size: Float
}

type UploadFileConnection {
  values: [UploadFile]
  groupBy: UploadFileGroupBy
  aggregate: UploadFileAggregator
}

type UploadFileConnectionAlternativeText {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionCaption {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionCreated_at {
  key: DateTime
  connection: UploadFileConnection
}

type UploadFileConnectionExt {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionFormats {
  key: JSON
  connection: UploadFileConnection
}

type UploadFileConnectionHash {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionHeight {
  key: Int
  connection: UploadFileConnection
}

type UploadFileConnectionId {
  key: ID
  connection: UploadFileConnection
}

type UploadFileConnectionMime {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionName {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionPreviewUrl {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionProvider {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionProvider_metadata {
  key: JSON
  connection: UploadFileConnection
}

type UploadFileConnectionSize {
  key: Float
  connection: UploadFileConnection
}

type UploadFileConnectionUpdated_at {
  key: DateTime
  connection: UploadFileConnection
}

type UploadFileConnectionUrl {
  key: String
  connection: UploadFileConnection
}

type UploadFileConnectionWidth {
  key: Int
  connection: UploadFileConnection
}

type UploadFileGroupBy {
  id: [UploadFileConnectionId]
  created_at: [UploadFileConnectionCreated_at]
  updated_at: [UploadFileConnectionUpdated_at]
  name: [UploadFileConnectionName]
  alternativeText: [UploadFileConnectionAlternativeText]
  caption: [UploadFileConnectionCaption]
  width: [UploadFileConnectionWidth]
  height: [UploadFileConnectionHeight]
  formats: [UploadFileConnectionFormats]
  hash: [UploadFileConnectionHash]
  ext: [UploadFileConnectionExt]
  mime: [UploadFileConnectionMime]
  size: [UploadFileConnectionSize]
  url: [UploadFileConnectionUrl]
  previewUrl: [UploadFileConnectionPreviewUrl]
  provider: [UploadFileConnectionProvider]
  provider_metadata: [UploadFileConnectionProvider_metadata]
}

type User {
  id: ID!
  live: Boolean!
  username: String
  contributor: Boolean!
  dateRegistered: DateTime
  about: String
  dateOfBirth: DateTime
  firstName: String
  lastName: String
  apiKey: UUID
  email: String
  registrationSource: UserRegistrationSource
  area: Area
  twitter: String
  website: String
  blog: String
  flickr: String
  youtube: String
  profileImage: String
  pronouns: String
  name: String
  country: Country
  imageUrl: String @deprecated
  image: String
  locale: String
  events(type: UserEventType!): [Event]
  adTargeting: [AdTargeting]
  managedEvents(artistId: Int, dateFrom: DateTime, dateTo: DateTime, order: SortOrderType, limit: Int): [Event]
  managedEventListings(dateFrom: DateTime, dateTo: DateTime, order: SortOrderType, page: Int!, pageSize: Int!): ManagedEventListings
  managedProfiles: ProfileManager
  managedArtists: [Artist]
  managedLabels: [Label]
  managedPromoters(ids: [ID]): [Promoter]
  promoterContactPermissions: [PromoterContactPermission]
  orders(limit: Int): [Order]
  hasBetaAccess: Boolean
  newMessagesCount: Int!
  newEventRevisionsCount: Int!
  followedProfilesCount: Int!
  permissions: [String]
  marketingCommunications: [MarketingCommunicationDto]
  isSubscribedToAllDefaultMarketingCommunications: Boolean!
  followedProfiles(filters: [FilterInput], sortField: FilterSortFieldType, sortOrder: FilterSortOrderType, page: Int, pageSize: Int): Listing
  recommendedProfiles(areaId: Int, pageSize: Int): RecommendedProfiles
  personalizedEvents(aggregations: [ListingAggregationType!], filters: FilterInputDtoInput, sort: SortInputDtoInput, page: Int, pageSize: Int): Listing
  personalizedEventListings(filters: FilterInputDtoInput, filterOptions: FilterOptionsInputDtoInput, sort: SortInputDtoInput, page: Int, pageSize: Int): EventListings
  savedEventListings(filters: FilterInputDtoInput, filterOptions: FilterOptionsInputDtoInput, sort: SortInputDtoInput, page: Int, pageSize: Int): EventListings
  externalArtists(provider: ExternalMusicProvider!, authToken: String, code: String): Listing
  iterableJwtToken: String
  mergedOrders: [MergedOrder]
  sourceSavedArtists(cursor: SourceSavedArtistWhereUniqueInput, distinct: [SourceSavedArtistScalarFieldEnum!], orderBy: [SourceSavedArtistOrderByWithRelationInput!], skip: Int, take: Int, where: SourceSavedArtistWhereInput): [SourceSavedArtist!]!
  sourceSavedArtistList(where: SourceSavedArtistListWhereUniqueInput!): SourceSavedArtistList!
  sourceSavedArtistLists(cursor: SourceSavedArtistListWhereUniqueInput, distinct: [SourceSavedArtistListScalarFieldEnum!], orderBy: [SourceSavedArtistListOrderByWithRelationInput!], skip: Int, take: Int, where: SourceSavedArtistListWhereInput): [SourceSavedArtistList!]!
  sourceRecommendations(args: SourceRecommendationsArgs!): [SourceRecommendation!]!
}

type UserAppSettings {
  id: ID!
  deviceId: UUID!
  devicePushToken: String!
  dateFirstLoggedIn: DateTime!
  dateLastOnline: DateTime!
  app: App!
  appVersion: String!
  platformId: Platform!
  platformOS: String!
  device: String!
}

type UserPermissionsPasswordPayload {
  ok: Boolean!
}

type UserRegisteredApp {
  id: ID!
  username: String
  email: String!
  apiKey: UUID!
  idToken: String!
  refreshToken: String!
  area: Area
}

type UsersPermissionsLoginPayload {
  jwt: String
  user: UsersPermissionsMe!
}

type UsersPermissionsMe {
  id: ID!
  username: String!
  email: String!
  confirmed: Boolean
  blocked: Boolean
  role: UsersPermissionsMeRole
}

type UsersPermissionsMeRole {
  id: ID!
  name: String!
  description: String
  type: String
}

type UsersPermissionsPermission {
  id: ID!
  type: String!
  controller: String!
  action: String!
  enabled: Boolean!
  policy: String
  role: UsersPermissionsRole
}

type UsersPermissionsRole {
  id: ID!
  name: String!
  description: String
  type: String
  permissions(sort: String, limit: Int, start: Int, where: JSON): [UsersPermissionsPermission]
  users(sort: String, limit: Int, start: Int, where: JSON): [UsersPermissionsUser]
}

type UsersPermissionsRoleAggregator {
  count: Int
  totalCount: Int
}

type UsersPermissionsRoleConnection {
  values: [UsersPermissionsRole]
  groupBy: UsersPermissionsRoleGroupBy
  aggregate: UsersPermissionsRoleAggregator
}

type UsersPermissionsRoleConnectionDescription {
  key: String
  connection: UsersPermissionsRoleConnection
}

type UsersPermissionsRoleConnectionId {
  key: ID
  connection: UsersPermissionsRoleConnection
}

type UsersPermissionsRoleConnectionName {
  key: String
  connection: UsersPermissionsRoleConnection
}

type UsersPermissionsRoleConnectionType {
  key: String
  connection: UsersPermissionsRoleConnection
}

type UsersPermissionsRoleGroupBy {
  id: [UsersPermissionsRoleConnectionId]
  name: [UsersPermissionsRoleConnectionName]
  description: [UsersPermissionsRoleConnectionDescription]
  type: [UsersPermissionsRoleConnectionType]
}

type UsersPermissionsUser {
  id: ID!
  created_at: DateTime!
  updated_at: DateTime!
  username: String!
  email: String!
  provider: String
  confirmed: Boolean
  blocked: Boolean
  role: UsersPermissionsRole
}

type UsersPermissionsUserAggregator {
  count: Int
  totalCount: Int
}

type UsersPermissionsUserConnection {
  values: [UsersPermissionsUser]
  groupBy: UsersPermissionsUserGroupBy
  aggregate: UsersPermissionsUserAggregator
}

type UsersPermissionsUserConnectionBlocked {
  key: Boolean
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserConnectionConfirmed {
  key: Boolean
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserConnectionCreated_at {
  key: DateTime
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserConnectionEmail {
  key: String
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserConnectionId {
  key: ID
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserConnectionProvider {
  key: String
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserConnectionRole {
  key: ID
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserConnectionUpdated_at {
  key: DateTime
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserConnectionUsername {
  key: String
  connection: UsersPermissionsUserConnection
}

type UsersPermissionsUserGroupBy {
  id: [UsersPermissionsUserConnectionId]
  created_at: [UsersPermissionsUserConnectionCreated_at]
  updated_at: [UsersPermissionsUserConnectionUpdated_at]
  username: [UsersPermissionsUserConnectionUsername]
  email: [UsersPermissionsUserConnectionEmail]
  provider: [UsersPermissionsUserConnectionProvider]
  confirmed: [UsersPermissionsUserConnectionConfirmed]
  blocked: [UsersPermissionsUserConnectionBlocked]
  role: [UsersPermissionsUserConnectionRole]
}

type ValidationSchemas {
  ticketing: Ticketing_ValidationSchemas
  guestlist: Guestlist_ValidationSchemas
}

type VenmoAccount implements IPaymentDetails {
  type: TransferMethodType!
  accountId: String!
  token: ID!
  status: String!
  createdOn: DateTime!
  transferMethodCountry: String!
  transferMethodCurrency: String!
}

type Venue implements IListingItem {
  id: ID!
  live: Boolean!
  capacity: String
  address: String
  phone: String
  raSays: Boolean
  tba: Boolean
  isClosed: Boolean
  area: Area
  country: Country
  website: String
  location: GeoLocation
  name: String
  listingItemId: Int!
  index: IndexType!
  blurb: SecureSanitizedHtml
  photo: String
  contentUrl: String
  logoUrl: String
  isFollowing: Boolean!
  news(limit: Int, excludeIds: [ID]): [News]
  followerCount: Int!
  eventCountThisYear: Int!
  topArtists: [Artist]
  events(limit: Int, type: EventQueryType!, excludeIds: [ID], year: Int, date: DateTime): [Event]
}

type createMetadataOverridePayload {
  metadataOverride: MetadataOverride
}

type createRolePayload {
  role: UsersPermissionsRole
}

type createUserPayload {
  user: UsersPermissionsUser
}

type deleteFilePayload {
  file: UploadFile
}

type deleteMetadataOverridePayload {
  metadataOverride: MetadataOverride
}

type deleteRolePayload {
  role: UsersPermissionsRole
}

type deleteUserPayload {
  user: UsersPermissionsUser
}

type updateMetadataOverridePayload {
  metadataOverride: MetadataOverride
}

type updateRolePayload {
  role: UsersPermissionsRole
}

type updateUserPayload {
  user: UsersPermissionsUser
}
```
