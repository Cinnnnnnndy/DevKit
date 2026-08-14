import {
  BaselineActPresenter,
  BuildDiagnosisActPresenter,
  ConfigActPresenter,
  LandingActPresenter,
  type MigrationActPresenterProps,
  PatchReviewActPresenter,
  PlanActPresenter,
  ProfileActPresenter,
  ReportActPresenter,
  SummaryActPresenter,
  TuningActPresenter,
} from "./presenters";

export function MigrationFlowView(props: MigrationActPresenterProps) {
  switch (props.state.act) {
    case 1:
      return <LandingActPresenter {...props} />;
    case 2:
      return <PlanActPresenter {...props} />;
    case 3:
      return <ConfigActPresenter {...props} />;
    case 4:
      return <ReportActPresenter {...props} />;
    case 5:
      return <PatchReviewActPresenter {...props} />;
    case 6:
      return <BuildDiagnosisActPresenter {...props} />;
    case 7:
      return <BaselineActPresenter {...props} />;
    case 8:
      return <TuningActPresenter {...props} />;
    case 9:
      return <ProfileActPresenter {...props} />;
    case 10:
      return <SummaryActPresenter {...props} />;
  }
}
