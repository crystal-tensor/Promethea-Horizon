import Mathlib.Data.Real.Basic

namespace B9

structure SpectralSummary where
  gap : Real
  width : Real
  normalizedGap : Real
  locality : Nat

section ClusterStabilizer
namespace ClusterStabilizer

def RawGapAmplifies (before after : SpectralSummary) : Prop :=
  after.gap > before.gap

def NormalizedGapInvariant (before after : SpectralSummary) : Prop :=
  after.normalizedGap = before.normalizedGap

def LocalityPreserved (before after : SpectralSummary) : Prop :=
  after.locality = before.locality

theorem uniform_scale_raw_gap_is_not_certificate
    (before after : SpectralSummary)
    (_hRaw : RawGapAmplifies before after)
    (hInvariant : NormalizedGapInvariant before after) :
    ¬ (after.normalizedGap > before.normalizedGap) := by
  intro hImp
  rw [hInvariant] at hImp
  exact (lt_irrefl before.normalizedGap) hImp

theorem cluster_stabilizer_open_uniform_reweight_obligation
    (n : Nat)
    (_hN : 4 <= n)
    (before after : SpectralSummary)
    (hLocality : LocalityPreserved before after)
    (hRaw : RawGapAmplifies before after)
    (hInvariant : NormalizedGapInvariant before after) :
    after.locality = before.locality ∧
      ¬ (after.normalizedGap > before.normalizedGap) := by
  constructor
  . exact hLocality
  . exact uniform_scale_raw_gap_is_not_certificate before after hRaw hInvariant

end ClusterStabilizer

end ClusterStabilizer

open ClusterStabilizer

section SupportSize

def HasSupportSize (summary : SpectralSummary) : Prop :=
  summary.locality = 2 ∨ summary.locality = 3

theorem locality_in_support_set (summary : SpectralSummary) (hLoc : HasSupportSize summary) :
    summary.locality = 2 ∨ summary.locality = 3 := hLoc

def MaxLocalityPreserved (before after : SpectralSummary) : Prop :=
  after.locality <= before.locality

theorem uniform_scale_preserves_max_locality
    (before after : SpectralSummary)
    (hLoc : LocalityPreserved before after) :
    MaxLocalityPreserved before after := by
  unfold MaxLocalityPreserved
  rw [hLoc]

end SupportSize

section UniformScaling

noncomputable def UniformScaleFactor : Real := 27/20

theorem uniform_scale_factor_nonzero : UniformScaleFactor ≠ 0 := by
  norm_num [UniformScaleFactor]

def IsUniformlyScaled (before after : SpectralSummary) : Prop :=
  after.gap = UniformScaleFactor * before.gap ∧
  after.width = UniformScaleFactor * before.width

theorem uniform_nonzero_scale_preserves_normalized_gap
    (gap width scale : Real)
    (before after : SpectralSummary)
    (hBefore : before.normalizedGap = gap / width)
    (hAfter : after.normalizedGap = (scale * gap) / (scale * width))
    (hScaleNonzero : scale ≠ 0) :
    ClusterStabilizer.NormalizedGapInvariant before after := by
  unfold ClusterStabilizer.NormalizedGapInvariant
  rw [hAfter, hBefore]
  exact mul_div_mul_left gap width hScaleNonzero

end UniformScaling

section SpectralWidth

def SpectralWidthPreserved (before after : SpectralSummary) : Prop :=
  after.width / after.gap = before.width / before.gap

theorem uniform_nonzero_scale_preserves_spectral_width_ratio
    (before after : SpectralSummary)
    (hScale : IsUniformlyScaled before after)
    (hScaleNonzero : UniformScaleFactor ≠ 0) :
    SpectralWidthPreserved before after := by
  rcases hScale with ⟨hGap, hWidth⟩
  unfold SpectralWidthPreserved
  rw [hGap, hWidth]
  exact mul_div_mul_left before.width before.gap hScaleNonzero

end SpectralWidth

end B9
